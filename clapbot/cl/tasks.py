import random
from pathlib import Path
from functools import wraps

import requests
from celery.utils.log import get_task_logger
from celery.canvas import group

from ..core import app, celery, db
from .model import Listing, Image
from .scrape import iter_scraped_results

__all__ = ['download_listing', 'download_image']

logger = get_task_logger(__name__)

class RequestsTask(celery.Task):
    """A task which retries when requests times out, with some jitter."""
    
    def __call__(self, *args, **kwargs):
        try:
           return super().__call__(*args, **kwargs)
        except requests.Timeout as exc:
            if self.request.retries > app.config.get("REQUESTS_MAX_RETRIES", 5):
                self.retry(exc=exc, countdown=int(random.uniform(2, 4) ** self.request.retries))
            raise

def requests_retry_task(**kwargs):
    """Ensure that retries for requests timeouts are properly handled."""
    kwargs['base'] = RequestsTask
    return celery.task(**kwargs)

def get_cached_url(url, path, save=False, description="item"):
    if save:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            logger.info(f"Loading {description} from cached file.")
            return path.read_bytes()
    logger.info(f"Requesting {description} from {url}.")
    response = requests.get(url, timeout=app.config.get("REQUESTS_TIMEOUT", 5))
    response.raise_for_status()
    if save:
        logger.info(f"Saving {description} to cacehd file.")
        path.write_bytes(response.content)
    return response.content

@requests_retry_task()
def download_listing(listing_id, force=False):
    """Download and parse a listing from craigslist"""
    listing = Listing.query.get(listing_id)

    if listing.text is None or force:
        path = listing.cache_path / f"{listing.cl_id}.html"
        save = app.config['CRAIGSLIST_CACHE_ENABLE']
        content = get_cached_url(listing.url, path, save=save, description=f"listing for {listing.cl_id}")
        listing.parse_html(content)

    db.session.commit()
    return listing_id

@celery.task()
def download_images_for_listing(listing_id, force=False):
    """Return the image ids for image fetching"""
    listing = Listing.query.get(listing_id)
    image_ids = [image.id for image in listing.images if (image.full is None or image.thumbnail is None) or force]
    image_group = group([download_image.si(img_id, force=force).set(countdown=int(random.uniform(0, 120))) for img_id in image_ids])
    return image_group.delay()

@requests_retry_task()
def download_image(image_id, force=False):
    """Download an image from craigslist"""
    image = Image.query.get(image_id)
    save = app.config['CRAIGSLIST_CACHE_ENABLE']

    if image.full is None or force:
        path = image.cache_path / f"{image.cl_id}.full.jpg"        
        content = get_cached_url(image.url, path, save=save, description=f'image (full) {image.cl_id}')
        image.full = content
    
    if image.thumbnail is None or force:
        path = image.cache_path / f"{image.cl_id}.thumbnail.jpg"
        content = get_cached_url(image.thumbnail_url, path, save=save, description=f"image (thumbnail) {image.cl_id}")
        image.thumbnail = content

    db.session.commit()
    return image_id

@celery.task
def ingest_listing(listing_json, force=False):
    listing = Listing.query.filter_by(cl_id=listing_json['id']).one_or_none()
    if (listing is not None) and (not force):
        # We've seen this lisitng before, don't ingest it.
        return listing.id
    
    save = app.config['CRAIGSLIST_CACHE_ENABLE']
    if listing is None:
        listing = Listing.from_result(listing_json)
    
    if save and not listing.cache_path.exists():
        with (listing.cache_path / '{}.json'.format(listing_json['id'])).open('w') as f:
            json.dump(listing_json, f)
    db.session.add(listing)
    app.logger.info("Added Craigslist entry for {0}".format(listing.cl_id))
    db.session.commit()
    return listing.id

def new_listing_pipeline(listing_json, force=False):
    return (ingest_listing.s(listing_json, force=force) | 
            download_listing.s(force=force).set(countdown=int(random.uniform(0, 120))) | 
            download_images_for_listing.s(force=force))

@celery.task
def scrape(limit=20, force=False):
    """Scrape listings from craigslist, and ingest them properly."""
    g = group([new_listing_pipeline(result, force=force) for result in iter_scraped_results(app, limit=limit)])
    return g.delay()
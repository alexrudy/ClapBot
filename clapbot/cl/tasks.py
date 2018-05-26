import random
import json
from pathlib import Path
from functools import wraps

import requests

from flask import current_app as app

from celery.utils.log import get_task_logger
from celery.canvas import group, chunks

from ..core import celery, db
from .model import Listing, Image
from . import scrape as cl_scrape

__all__ = ['download_listing', 'download_image']

logger = get_task_logger(__name__)


class RequestsTask(celery.Task):
    """A task which retries when requests times out, with some jitter."""

    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)
        except requests.Timeout as exc:
            print("Caught timeout, retrying: {}/{}".format(
                self.request.retries, self.max_retries))
            self.retry(
                exc=exc,
                countdown=int(random.uniform(2, 4)**self.request.retries))


def requests_retry_task(**kwargs):
    """Ensure that retries for requests timeouts are properly handled."""
    kwargs['base'] = RequestsTask
    kwargs.setdefault('max_retries', 5)
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
        content = get_cached_url(
            listing.url,
            path,
            save=save,
            description=f"listing for {listing.cl_id}")
        listing.parse_html(content)t

    db.session.commit()
    return listing_id


@celery.task()
def download_images_for_listing(listing_id, force=False):
    """Return the image ids for image fetching"""
    listing = Listing.query.get(listing_id)
    image_ids = [
        image.id for image in listing.images
        if (image.full is None or image.thumbnail is None) or force
    ]
    image_group = group(
        [download_image.si(img_id, force=force) for img_id in image_ids])
    result = image_group.skew(
        start=1, stop=app.config['CRAIGSLIST_TASK_SKEW']).delay()
    result.save()
    return result.id


@requests_retry_task()
def download_image(image_id, force=False):
    """Download an image from craigslist"""
    image = Image.query.get(image_id)
    save = app.config['CRAIGSLIST_CACHE_ENABLE']

    if image.full is None or force:
        path = image.cache_path / f"{image.cl_id}.full.jpg"
        content = get_cached_url(
            image.url,
            path,
            save=save,
            description=f'image (full) {image.cl_id}')
        image.full = content

    if image.thumbnail is None or force:
        path = image.cache_path / f"{image.cl_id}.thumbnail.jpg"
        content = get_cached_url(
            image.thumbnail_url,
            path,
            save=save,
            description=f"image (thumbnail) {image.cl_id}")
        image.thumbnail = content

    db.session.add(image)
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
    path = (listing.cache_path / '{}.json'.format(listing_json['id']))
    if save and not path.exists():
        with path.open('w') as f:
            json.dump(listing_json, f)
    db.session.add(listing)
    app.logger.info("Added Craigslist entry for {0}".format(listing.cl_id))
    db.session.commit()
    return listing.id


def new_listing_pipeline(listing_json, force=False):
    """Task pipeline to transform new listing JSON into a listing record and associated images."""
    return (ingest_listing.s(listing_json, force=force)
            | download_listing.s(force=force).set(
                countdown=int(
                    random.uniform(0, app.config['CRAIGSLIST_TASK_SKEW'])))
            | download_images_for_listing.s(force=force))


@celery.task
def scrape(limit=None, force=False):
    """Scrape listings from craigslist, and ingest them properly."""
    limit = limit if limit is not None else app.config['CRAIGSLIST_MAX_SCRAPE']
    g = group([
        new_listing_pipeline(result, force=force)
        for result in cl_scrape.iter_scraped_results(app, limit=limit)
    ])
    result = g.delay()
    result.save()
    return result.id


@celery.task
def export_listing(listing_id, force=False):
    """Dump this listing to disk if needed."""
    listing = Listing.query.get(listing_id)
    save = app.config['CRAIGSLIST_CACHE_ENABLE']
    path = (listing.cache_path / '{}.json'.format(listing.cl_id))
    if save and ((not path.exists()) or force):
        logger.info(f"Saving {listing} to cacehd file.")
        with path.open('w') as f:
            json.dump(listing.to_json(), f)
    return listing_id


@celery.task
def export_listings(force=False):
    """Ensure listing infor is saved to disk."""
    exporters = group([
        export_listing.s(listing.id, force=force) for listing in Listing.query
    ])
    result = exporters.skew(
        start=1, stop=app.config['CRAIGSLIST_TASK_SKEW']).delay()
    result.save()
    return result.id


@celery.task
def ensure_downloaded(force=False):
    """Ensure that listings and images are downloaded to disk."""

    # Can't filter on text==None here because we want to download images as well.
    listings = Listing.query

    downloaders = group([(download_listing.si(listing.id, force=force)
                          | download_images_for_listing.s(force=force))
                         for listing in listings])
    result = downloaders.skew(
        start=1, stop=app.config['CRAIGSLIST_TASK_SKEW']).delay()
    result.save()
    return result.id

# -*- coding: utf-8 -*-

from . import celery, app, db
from .model import Listing
from . import scrape
from . import location
from .notify import send_notification

def instrument_listing(listing_id):
    """Instrument everything necessary for a given listing."""
    return download.si(listing_id) | download_images.si(listing_id) | location_info.si(listing_id)

@celery.task(ignore_result=True)
def scraper():
    """Scrape craigslist."""
    scrape.scrape(db.session, limit=app.config['CRAIGSLIST_MAX_SCRAPE'])

@celery.task(ignore_result=True)
def notify():
    """Notify by sending an email."""
    listings = Listing.query.order_by(Listing.created).filter_by(notified=False).limit(app.config['CRAIGSLIST_MAX_MAIL'])
    if listings.count():
        send_notification(listings.all())

@celery.task(ignore_result=True)
def download(listing_id, save=False):
    """Download a listing."""
    listing = Listing.query.get(listing_id)
    path = app.config['CRAIGSLIST_CACHE_PATH']
    scrape.download_listing(listing, path, save=save)
    db.session.commit()

@celery.task(ignore_result=True)
def download_images(listing_id, save=False, force=False):
    """Download images."""
    listing = Listing.query.get(listing_id)
    path = app.config['CRAIGSLIST_CACHE_PATH']
    scrape.download_images(listing, path, save=save)
    db.session.commit()
    
@celery.task(ignore_result=True)
def location_info(listing_id):
    """Find the nearest stop for a listing."""
    listing = Listing.query.get(listing_id)
    if not location.check_inside_bboxes(listing):
        db.session.delete(listing)
    else:
        location.find_nearest_transit_stop(listing)
    db.session.commit()
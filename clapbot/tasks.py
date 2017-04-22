# -*- coding: utf-8 -*-

from . import celery, app, db
from .model import Listing
from . import scrape
from . import location

@celery.task()
def scrape_craigslist():
    """Request that the scraper run."""
    pass

@celery.task()
def download(listing_id, save=False):
    """Download a listing."""
    listing = Listing.query.get(listing_id)
    path = app.config['CRAIGSLIST_CACHE_PATH']
    scrape.download_listing(listing, path, save=save)
    db.session.commit()

@celery.task()
def download_images(listing_id, save=False, force=False):
    """Download images."""
    listing = Listing.query.get(listing_id)
    path = app.config['CRAIGSLIST_CACHE_PATH']
    scrape.download_images(listing, path, save=save)
    db.session.commit()
    
@celery.task()
def location_info(listing_id):
    """Find the nearest stop for a listing."""
    listing = Listing.query.get(listing_id)
    location.find_nearest_transit_stop(listing)
    db.session.commit()
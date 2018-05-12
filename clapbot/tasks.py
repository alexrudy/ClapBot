# -*- coding: utf-8 -*-

from celery.schedules import crontab
import os
from sqlalchemy import or_

from . import celery, app, db
from .model import Listing, UserListingInfo
from . import scrape
from . import location
from .notify import send_notification
from .score import score_all

def instrument_listing(listing_id):
    """Instrument everything necessary for a given listing."""
    return download.si(listing_id) | download_images.si(listing_id) | location_info.si(listing_id) | score.si(listing_id)

@celery.task(ignore_result=True)
def score(listing_id):
    """Score listings"""
    listing = Listing.query.get(listing_id)
    if listing is None:
        return
    score_all(listing)
    db.session.add(listing.userinfo)
    db.session.commit()
    return listing.userinfo.score

@celery.task(ignore_result=True)
def scraper():
    """Scrape craigslist."""
    scrape.scrape(db.session, limit=app.config['CRAIGSLIST_MAX_SCRAPE'], save=app.config['CRAIGSLIST_CACHE_ENABLE'])

@celery.task(ignore_result=True)
def notify():
    """Notify by sending an email."""
    listings = Listing.query.filter(Listing.transit_stop_id != None)
    listings = listings.order_by(Listing.created.desc()).filter_by(notified=False)
    listings = listings.from_self().join(UserListingInfo, isouter=True).filter(or_(~UserListingInfo.rejected,UserListingInfo.rejected == None))
    listings = listings.order_by(UserListingInfo.score.desc()).filter(UserListingInfo.score > 0)
    listings = listings.limit(app.config['CRAIGSLIST_MAX_MAIL'])
    if listings.count() and app.config['CRAIGSLIST_SEND_MAIL']:
        send_notification(listings.all())
    else:
        print("Would have notified about {0:d} listings".format(listings.count()))

@celery.task(ignore_result=True)
def download(listing_id):
    """Download a listing."""
    listing = Listing.query.get(listing_id)
    path = os.path.join(app.instance_path, app.config['CRAIGSLIST_CACHE_PATH'])
    scrape.download_listing(listing, path, save=app.config['CRAIGSLIST_CACHE_ENABLE'])
    db.session.commit()

@celery.task(ignore_result=True)
def download_images(listing_id, force=False):
    """Download images."""
    listing = Listing.query.get(listing_id)
    path = os.path.join(app.instance_path, app.config['CRAIGSLIST_CACHE_PATH'])
    scrape.download_images(listing, path, save=app.config['CRAIGSLIST_CACHE_ENABLE'])
    db.session.commit()
    
@celery.task(ignore_result=True)
def location_info(listing_id):
    """Find the nearest stop for a listing."""
    listing = Listing.query.get(listing_id)
    bbox_flag = app.config['CRAIGSLIST_CHECK_BBOX']
    if (not location.check_inside_bboxes(listing)) and bbox_flag:
        db.session.delete(listing)
    else:
        location.find_nearest_transit_stop(listing)
    db.session.commit()
    
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    
    # Executes every 15 minutes.
    sender.add_periodic_task(
        crontab(minute='*/15'),
        scraper.s(),
    )
    
    # Executes every hour during the day.
    sender.add_periodic_task(
        crontab(minute=0, hour='0-5,12-23'),
        notify.s(),
    )
# -*- coding: utf-8 -*-
from flask import current_app as app

from celery.schedules import crontab
from sqlalchemy import or_

from .core import db, celery
from .model import UserListingInfo
from .cl.model import Listing
from . import location
from .notify import send_notification
from .score import score_all

# pylint: disable=unused-import
from .cl import tasks  # noqa: F401


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
def notify():
    """Notify by sending an email."""
    # pylint: disable=singleton-comparison
    listings = Listing.query.filter(
        Listing.transit_stop_id != None)  # noqa: E711
    listings = listings.order_by(
        Listing.created.desc()).filter_by(notified=False)
    listings = listings.from_self().join(
        UserListingInfo, isouter=True).filter(
            or_(~UserListingInfo.rejected,
                UserListingInfo.rejected == None))  # noqa: E711

    listings = listings.order_by(
        UserListingInfo.score.desc()).filter(UserListingInfo.score > 0)
    listings = listings.limit(app.config['CRAIGSLIST_MAX_MAIL'])
    if listings.count() and app.config['CRAIGSLIST_SEND_MAIL']:
        send_notification(listings.all())
    else:
        print("Would have notified about {0:d} listings".format(
            listings.count()))


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
    # pylint: disable=unused-argument
    # Executes every hour during the day.
    sender.add_periodic_task(
        crontab(minute=0, hour='0-5,12-23'),
        notify.s(),
    )

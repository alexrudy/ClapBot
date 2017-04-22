# -*- coding: utf-8 -*-

import craigslist
import requests
import click

import os
import glob
import datetime as dt
import json
import itertools

from .application import app, db
from .model import Listing

class CraigslistHousing(craigslist.CraigslistHousing):
    """Set up a custom query for craigslist housing"""
    
    @classmethod
    def from_app(cls, app, site=None, area=None):
        """Make a housing query from an application object."""
        site = site or app.config['CRAIGSLIST_SITE']
        area = area or app.config['CRAIGSLIST_AREA']
        return cls(site=site, area=area, category=app.config['CRAIGSLIST_CATEGORY'], filters=app.config['CRAIGSLIST_FILTERS'])

def safe_iterator(iterable, limit):
    """Safe iterator, which just logs problematic entries."""
    iterator = itertools.islice(iterable, limit)
    while True:
        try:
            gen = next(iterator)
        except StopIteration:
            break
        except Exception as e:
            app.logger.exception("Exception in craigslist result")
        else:
            yield gen

def scrape_to_json(path, limit=20):
    """Do a single scrape from craigslist and dump to JSON."""
    os.makedirs(path, exist_ok=True)
    query = CraigslistHousing.from_app(app)
    for result in tqdm(safe_iterator(query.get_results(sort_by='newest', geotagged=True, limit=limit), limit=limit), total=limit):
        filename = os.path.join(path, "{0}.json".format(result['id']))
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump(result, f)

def ingest_result(session, result):
    """Ingest a single result into the session."""
    listing = session.query(Listing).filter_by(cl_id=result['id']).one_or_none()
    path = app.config['CRAIGSLIST_CACHE_PATH']
    filename = os.path.join(path, "{0}.json".format(result['id']))
    
    if listing is not None:
        # We've seen this lisitng before, don't ingest it.
        return
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump(result, f)
    listing = Listing.from_result(result)
    session.add(listing)
    app.logger.info("Added Craigslist entry for {0}".format(listing.cl_id))

    

def scrape(session, site=None, area=None, limit=20):
    """Do a single scrape from craigslist and commit to the database."""
    query = CraigslistHousing.from_app(app, site=site, area=area)
    for result in safe_iterator(query.get_results(sort_by='newest', geotagged=True, limit=limit), limit=limit):
        ingest_result(session, result)
    
def download_images(listing, path, save=False, force=False):
    """Download the images which belong to a single listing."""
    for image in listing.images:
        full_name = os.path.join(path, f"{image.cl_id}.full.jpg")
        thumb_name = os.path.join(path, f"{image.cl_id}.thumb.jpg")
        if (image.full is None) and os.path.exists(full_name):
            with open(full_name, 'rb') as f:
                image.full = f.read()
            with open(thumb_name, 'rb') as f:
                image.thumbnail = f.read()
        elif force or (image.full is None):
            image.download()
            db.session.add(image)
        if save and not os.path.exists(full_name):
            with open(full_name, 'wb') as f:
                f.write(image.full)
            with open(thumb_name, 'wb') as f:
                f.write(image.thumbnail)
    
def download_listing(listing, path, save=False):
    """Using a single listing, download and save html if asked"""
    filename = os.path.join(path, f"{listing.cl_id}.html")
    
    # Download page.
    if save and os.path.exists(filename):
        with open(filename, 'rb') as f:
            listing.parse_html(f.read())
    else:
        listing.download()
        if save:
            with open(filename, 'wb') as f:
                f.write(listing.page)



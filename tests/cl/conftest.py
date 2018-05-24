import os
import json
from collections import Counter

import pytest

from clapbot.core import celery, db
from clapbot.cl import model

from httmock import urlmatch, HTTMock

@pytest.fixture
def listing(app):
    """Add a listing object to the db"""
    with app.app_context():
        listing =  model.Listing(cl_id=6095797875,
                                    url='http://sfbay.craigslist.org/eby/apa/6095797875.html',
                                    created='2017-04-22 09:26',
                                    available='2017-05-05',
                                    name='2 Bed - 2 Bath, Open House is this weekend! $2000 off specials!',
                                    price='$3029',
                                    location='6250 Stoneridge Mall Road, Pleasanton, CA 94588',
                                    lat=37.6936, lon=-121.9228)

        db.session.add(listing)
        db.session.commit()
        return listing.id


@pytest.fixture
def image(app):
    """Add an image object to the db"""
    with app.app_context():
        img = model.Image(url="https://images.craigslist.org/00E0E_fUsmqInrJwB_600x450.jpg")
        db.session.add(img)
        db.session.commit()
        return img.id

@pytest.fixture
def listing_json():
    """Return a single listing"""
    filename = os.path.join(os.path.dirname(__file__), "listing.json")
    with open(filename, 'r') as f:
        return json.load(f)
    
@pytest.fixture
def listing_html():
    """Return the HTML content for a listing."""
    filename = os.path.join(os.path.dirname(__file__), "listing.html")
    with open(filename, 'r') as f:
        return f.read()

@pytest.fixture
def image_data():
    # filename = os.path.join(os.path.dirname(__file__), "image.full.jpg")
    # with open(filename, 'rb') as f:
    #     return f.read()
    return b"IMAGE DATA"


@pytest.fixture
def craigslist(monkeypatch, listing_json, listing_html, image_data):

    def iter_listings(app, **kwargs):
        print("Scraping from {kwargs}")
        yield listing_json

    monkeypatch.setattr('clapbot.cl.scrape.iter_scraped_results', iter_listings)
    
    urls = Counter()

    @urlmatch(netloc=r'(.*\.)?craigslist\.org$')
    def load_listing(url, request):
        print(f"Returning some listing data for {url}")
        urls[url] += 1
        return listing_html

    @urlmatch(netloc=r'images\.craigslist\.org$')
    def load_image(url, request):
        print(f"Returning some image data for {url}")
        urls[url] += 1
        return image_data

    with HTTMock(load_listing, load_image):
        yield urls
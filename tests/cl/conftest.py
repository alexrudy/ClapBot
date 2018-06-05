import os
import json
import logging
from urllib.parse import urlunsplit
from collections import Counter

import pytest

import requests
from httmock import urlmatch, HTTMock, all_requests

from clapbot.core import db
from clapbot.cl import model

log = logging.getLogger('__name__')

# pylint: disable=redefined-outer-name,unused-argument


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
def listing(app, listing_json):
    """Add a listing object to the db"""
    with app.app_context():
        listing = model.Listing.from_result(listing_json)
        db.session.add(listing)
        db.session.commit()
        return listing.id


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
        log.info(f"Scraping from {kwargs!r}")
        yield listing_json

    monkeypatch.setattr('clapbot.cl.scrape.iter_scraped_results', iter_listings)

    urls = Counter()

    @urlmatch(netloc=r'(.*\.)?craigslist\.org$')
    def load_listing(url, request):
        log.info(f"Returning some listing data for {url}")
        urls[urlunsplit(url)] += 1
        return listing_html

    @urlmatch(netloc=r'images\.craigslist\.org$')
    def load_image(url, request):
        log.info(f"Returning some image data for {url}")
        urls[urlunsplit(url)] += 1
        return image_data

    with HTTMock(load_image, load_listing):
        yield urls


@pytest.fixture
def nointernet():
    """Block internet access in requests."""
    urls = Counter()

    @all_requests
    def timeout_mock(url, request):
        urls[urlunsplit(url)] += 1
        raise requests.ConnectTimeout(f"Connection timeout: {urlunsplit(url)}")

    with HTTMock(timeout_mock):
        yield urls


@pytest.fixture
def missingpages():
    urls = Counter()

    @all_requests
    def timeout_mock(url, request):
        urls[urlunsplit(url)] += 1
        return {'status_code': 404, 'content': 'Missing'}

    with HTTMock(timeout_mock):
        yield urls

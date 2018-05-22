# -*- coding: utf-8 -*-

import pytest
import json
import os

from unittest.mock import patch

from clapbot.cl import model
from clapbot.cl import tasks
from clapbot.core import db

from httmock import urlmatch, HTTMock

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
    filename = os.path.join(os.path.dirname(__file__), "image.full.jpg")
    with open(filename, 'rb') as f:
        return f.read()


@pytest.fixture
def craigslist(listing_html):

    @urlmatch(netloc=r'(.*\.)?craigslist\.org$')
    def load_listing(url, request):
        return listing_html

    with HTTMock(load_listing):
        yield
    
@pytest.fixture
def craigslist_image(image_data):

    @urlmatch(netloc=r'images\.craigslist\.org$')
    def load_image(url, request):
        return image_data

    with HTTMock(load_image):
        yield


@pytest.fixture
def listing(app):
    """Return an example listing"""
    listing = model.Listing.query.filter_by(cl_id=6098474009).one_or_none()
    if listing:
        return listing

    # Add to the database
    listing =  model.Listing(cl_id=6098474009,
            url='http://sfbay.craigslist.org/eby/apa/6098474009.html',
            created='2017-04-22 08:35',
            available='2017-05-05',
            name='COME ENJOY YOUR NEW HOME!',
            price='$1590',
            location='pittsburg / antioch')
    db.session.add(listing)
    db.session.flush()
    return listing

@pytest.fixture
def image_id(app):
    with app.app_context():
        img = model.Image.query.filter_by(url="https://images.craigslist.org/00E0E_fUsmqInrJwB_600x450.jpg").one_or_none()
        if not img:
            img = model.Image(url="https://images.craigslist.org/00E0E_fUsmqInrJwB_600x450.jpg")
            db.session.add(img)
            db.session.flush()
        return img.id

@pytest.fixture
def listing_id(listing):
    return listing.id    

def test_listing_from_json(app, listing_json):
    """Test making a listing from JSON"""
    with app.app_context():
        listing_id = tasks.ingest_listing(listing_json)
        assert listing_id
    
def test_listing_parse_html(app, listing, listing_html):
    """Test parsing HTML for listings"""
    with app.app_context():
        assert listing.bedrooms == None
        assert listing.bathrooms == None 
        listing.parse_html(listing_html)
        assert listing.bedrooms == 1
        assert listing.bathrooms == 1
        assert len(listing.images) == 1
        assert len(listing.text)
        assert len(listing.tags) == 5


def test_listing_download(app, craigslist, listing_id):
    with app.app_context():
        tasks.download_listing(listing_id)
        listing = model.Listing.query.get(listing_id)

        assert listing.bedrooms == 1
        assert listing.bathrooms == 1
        assert len(listing.images) == 1
        assert len(listing.text)
        assert len(listing.tags) == 5

def test_image_download(app, craigslist_image, image_id):
    with app.app_context():
        tasks.download_image(image_id)
        img = model.Image.query.get(image_id)
        assert img.full is not None

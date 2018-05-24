import pytest
import json
import os

from celery.result import GroupResult, AsyncResult

from clapbot.cl import tasks, model
from clapbot.core import db

def test_export_listing(app, celery_worker, celery_timeout, listing, listing_json):
    """Test the task which exports a single listing to a cache file."""
    assert app.config['CRAIGSLIST_CACHE_ENABLE']

    tasks.export_listing.s(listing).delay().get(timeout=celery_timeout)

    with app.app_context():
        cache_path = model.Listing.query.get(listing).cache_path
    assert_cache_json(cache_path, listing_json)

def assert_cache_json(cache_path, listing_json):
    paths = list(cache_path.glob('*.json'))
    assert len(paths) == 1

    path = next(iter(paths))
    exported_json = json.loads(path.read_text())
    
    for key, value in exported_json.items():
        if isinstance(value, (int, str)):
            assert exported_json[key] == listing_json[key], f"Mismatch for {key}"

def test_listing_download(app, celery_worker, celery_timeout, craigslist, listing):
    """Test the task which downloads a listing from craigslist."""
    with app.app_context():
        assert not model.Listing.query.get(listing).text

    tasks.download_listing.s(listing).delay().get(timeout=celery_timeout)

    with app.app_context():
        listing = model.Listing.query.get(listing)
        assert listing.bedrooms == 1
        assert listing.bathrooms == 1
        assert len(listing.images) == 1
        assert listing.text
        assert len(listing.tags) == 5

def test_image_download(app, celery_worker, celery_timeout, craigslist, image):
    """Test the task which downloads an image from craigslist"""
    with app.app_context():
        assert model.Image.query.get(image).full is None
        
    tasks.download_image.s(image).delay().get(timeout=celery_timeout)

    with app.app_context():
        assert model.Image.query.get(image).full is not None

def test_download_chain(app, celery_app, celery_worker, celery_timeout, craigslist, listing_json):
    
    with app.app_context():
        group = tasks.new_listing_pipeline(listing_json)
        
    result = group.delay().get(timeout=celery_timeout)
    GroupResult.restore(result[0], app=celery_app).get(timeout=celery_timeout)
    
    with app.app_context():

        listing = model.Listing.query.first()
        assert listing.bedrooms == 1
        assert listing.bathrooms == 1
        assert len(listing.images) == 1
        assert listing.text
        assert len(listing.tags) == 5

        img = model.Image.query.first()
        assert img.full is not None

def test_export_all(app, celery_app, celery_worker, celery_timeout, listing, listing_json):
    
    r = tasks.export_listings.delay().get(timeout=celery_timeout)
    GroupResult.restore(r[0], app=celery_app).get(timeout=celery_timeout)

    with app.app_context():
        cache_path = model.Listing.query.get(listing).cache_path
    assert_cache_json(cache_path, listing_json)

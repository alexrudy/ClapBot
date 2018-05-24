import pytest
import json
import os

from clapbot.cl import tasks, model
from clapbot.core import db

def test_listing_from_json(app, listing_json):
    """Test making a listing from JSON"""
    listing_id = tasks.ingest_listing(listing_json)
    assert listing_id
    
def test_listing_parse_html(app_context, listing, listing_html):
    """Test parsing HTML for listings"""
    listing = model.Listing.query.get(listing)
    assert listing.bedrooms == None
    assert listing.bathrooms == None 
    listing.parse_html(listing_html)
    assert listing.bedrooms == 1
    assert listing.bathrooms == 1
    assert len(listing.images) == 1
    assert len(listing.text)
    assert len(listing.tags) == 5

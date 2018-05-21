# -*- coding: utf-8 -*-

import pytest
import json
import os

from clapbot.model import Listing

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
def listing():
    """Return an example listing"""
    return Listing(cl_id=6098474009,
            url='http://sfbay.craigslist.org/eby/apa/6098474009.html',
            created='2017-04-22 08:35',
            available='2017-05-05',
            name='COME ENJOY YOUR NEW HOME!',
            price='$1590',
            location='pittsburg / antioch')
    
def test_listing_from_json(listing_json):
    """Test making a listing from JSON"""
    listing = Listing.from_result(listing_json)
    
def test_listing_parse_html(listing, listing_html):
    """Test parsing HTML for listings"""
    listing.parse_html(listing_html)
    assert listing.bedrooms == 1
    assert listing.bathrooms == 1
    assert len(listing.images) == 1
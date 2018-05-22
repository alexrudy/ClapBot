# -*- coding: utf-8 -*-

import click
import requests
import base64
import datetime as dt
from pathlib import Path
try:
    import urlparse as urlparse
except ImportError:
    import urllib.parse as urlparse

from bs4 import BeautifulSoup

from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import BigInteger

from .application import app, db
from .utils import coord_distance

from .cl.model import *
    
class BoundingBox(db.Model):
    """A bounding box"""
    __tablename__ = 'boundingbox'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    lat_min = db.Column(db.Float)
    lon_min = db.Column(db.Float)
    lat_max = db.Column(db.Float)
    lon_max = db.Column(db.Float)
    
    def contains(self, lat, lon):
        """docstring for contains"""
        if self.lat_min <= lat <= self.lat_max and self.lon_min <= lon <= self.lon_max:
            return True
        return False
    
class TransitStop(db.Model):
    """Transit stop model"""
    __tablename__ = 'transitstop'
    
    id = db.Column(db.Integer, primary_key=True)
    stop_id = db.Column(db.String)
    agency = db.Column(db.String)
    name = db.Column(db.String)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)


    
class UserListingInfo(db.Model):
    """Listing help information from the user."""
    
    __tablename__ = 'userlistinginfo'
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))
    listing = db.relationship("Listing", backref=db.backref("_userinfo", uselist=False))
    rejected = db.Column(db.Boolean, default=False)
    starred = db.Column(db.Boolean, default=False)
    contacted = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default="")


def init_db():
    """Initialize the database."""
    db.create_all()
    
@app.cli.command("initdb")
def init_db_command():
    """Initalize the database."""
    init_db()
    click.secho("Initialized the databse.", fg='green')
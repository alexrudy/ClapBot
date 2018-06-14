# -*- coding: utf-8 -*-

from .core import db


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
    listing = db.relationship("Listing", backref=db.backref("expiration_checks", uselist=True))
    rejected = db.Column(db.Boolean, default=False)
    starred = db.Column(db.Boolean, default=False)
    contacted = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default="")


def init_db():
    """Initialize the database."""
    db.create_all()

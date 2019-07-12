from ...core import db

import enum


class Result(enum.Enum):
    FAILURE = 0
    SUCCESS = 1
    ERROR = 2


class ListingScore(db.Model):
    __tablename__ = 'listingscore'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(255))
    score = db.Column(db.Integer)
    result = db.Column(db.Enum(Result))
    created_at = db.Column(db.DateTime)

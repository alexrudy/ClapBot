import base64
import logging
import urllib.parse

from pathlib import Path

from flask import current_app as app

from ...core import db

__all__ = ['images', 'Image']

logger = logging.getLogger(__name__)

images = db.Table(
    'images',
    db.Column('image_id', db.Integer, db.ForeignKey('image.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
)


class Image(db.Model):
    """Image belonging to a listing."""
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, unique=True)
    full = db.Column(db.LargeBinary)
    thumbnail = db.Column(db.LargeBinary)

    @property
    def cache_path(self):
        """Where to find cached image files."""
        path = Path(app.config['CRAIGSLIST_CACHE_PATH']) / 'images' / '{}'.format(self.cl_id)[:3]
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def thumbb64(self):
        """A thumbnail in base64"""
        return base64.b64encode(self.thumbnail).decode('ascii')

    @property
    def fullb64(self):
        """A full image in base64"""
        return base64.b64encode(self.full).decode('ascii')

    @property
    def cl_id(self):
        """Craigslist identifier."""
        #: https://images.craigslist.org/00d0d_1qTvVaQpLrT_600x450.jpg
        url = urllib.parse.urlsplit(self.url)
        return "_".join(url.path.lstrip("/").split("_")[:-1])

    @property
    def thumbnail_url(self):
        """Try to guess a thumbnail URL"""
        #: https://images.craigslist.org/00d0d_1qTvVaQpLrT_600x450.jpg
        url = urllib.parse.urlsplit(self.url)
        last_part, _ = url.path.split("_")[-1].split(".")
        try:
            [int(part) for part in last_part.split("x")]
        except ValueError:
            # We don't know that the thumbnail is really valid.
            return self.url
        else:
            scheme, netloc, path, query, fragment = url
            path = self.cl_id + "_50x50c.jpg"
            return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))

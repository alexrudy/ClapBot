import base64
import logging
import datetime as dt
import urllib.parse

from pathlib import Path

from flask import current_app as app

from bs4 import BeautifulSoup

from sqlalchemy.orm import validates
from sqlalchemy.types import BigInteger

from ..utils import coord_distance
from ..core import db

__all__ = ['images', 'tags', 'Image', 'Listing', 'Tag']

logger = logging.getLogger(__name__)

tags = db.Table(
    'tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
)

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


class Tag(db.Model):
    """A simple craigslist tag."""
    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

    @property
    def display_name(self):
        """Short display name"""
        name = self.name
        if ' - ' in name:
            name = name.split(' - ')[0].strip()
        if name.endswith('are OK'):
            name = name.replace('are OK', 'OK')
        if 'w/d ' in name:
            name = name.replace('w/d ', 'W/D ')
        return name


class Listing(db.Model):
    """Craigslist Listing"""
    __tablename__ = 'listing'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, unique=True)
    created = db.Column(db.DateTime)
    available = db.Column(db.Date)
    expired = db.Column(db.DateTime)

    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

    name = db.Column(db.String)
    price = db.Column(db.Float)
    location = db.Column(db.String)
    cl_id = db.Column(BigInteger, unique=True)

    area = db.Column(db.String)
    transit_stop_id = db.Column(db.Integer, db.ForeignKey("transitstop.id"))
    transit_stop = db.relationship("clapbot.model.TransitStop", backref=db.backref('listings', lazy='dynamic'))

    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    size = db.Column(db.Float)

    text = db.Column(db.Text)
    page = db.Column(db.Text)

    tags = db.relationship('Tag', secondary=tags, backref=db.backref('listings', lazy='dynamic'))
    images = db.relationship('Image', secondary=images, backref=db.backref('listings', lazy='dynamic'))

    notified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Listing(id={self.id} cl={self.cl_id})"

    @property
    def transit_stop_distance(self):
        """Distance to the transit stop"""
        return self.distance_to(self.transit_stop.lat, self.transit_stop.lon)

    @property
    def cache_path(self):
        """Where to find cached listings"""
        path = Path(app.config['CRAIGSLIST_CACHE_PATH']) / 'listings' / '{}'.format(self.cl_id)[:3]
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def score_info(self):
        """Return the score info for a listing."""
        from ..score import score_info
        return score_info(self)

    def distance_to(self, lat, lon):
        """Distance to some position."""
        return coord_distance(self.lat, self.lon, lat, lon)

    def distance_to_work(self):
        """Distance to work."""
        lat = app.config['CRAIGSLIST_SCORE_WORK_LAT']
        lon = app.config['CRAIGSLIST_SCORE_WORK_LON']
        return self.distance_to(lat, lon)

    @validates("created")
    def validate_datetime(self, key, value):
        """Validate a datetime"""
        # pylint: disable=unused-argument
        if isinstance(value, dt.datetime):
            return value
        return dt.datetime.strptime(value, "%Y-%m-%d %H:%M")

    @validates("available")
    def validate_date(self, key, value):
        """Validate a date object"""
        # pylint: disable=unused-argument
        if isinstance(value, dt.date):
            return value
        return dt.datetime.strptime(value, "%Y-%m-%d").date()

    @validates('price')
    def validate_price(self, key, value):
        """Validate price."""
        # pylint: disable=unused-argument
        if isinstance(value, float):
            return value
        return float(value.replace("$", ""))

    @validates('images')
    def validate_images(self, key, url):
        """Validate tag lists"""
        # pylint: disable=unused-argument
        if isinstance(url, Image):
            return url
        img = Image.query.filter_by(url=url).one_or_none()
        if img is not None:
            return img
        img = Image(url=url)
        db.session.add(img)
        return img

    @validates('tags')
    def validate_tags(self, key, name):
        """Validate tag lists"""
        # pylint: disable=unused-argument
        if isinstance(name, Tag):
            return name
        tag = Tag.query.filter_by(name=name).one_or_none()
        if tag is not None:
            return tag
        tag = Tag(name=name)
        db.session.add(tag)
        return tag

    def to_json(self):
        """Return the JSON-compatible structure which could create this object."""
        result = {
            'id': str(self.cl_id),
            'datetime': self.created.strftime('%Y-%m-%d %H:%M'),
            'where': self.location,
            'url': self.url,
            'price': f"${self.price:.0f}",
            'name': self.name,
            'geotag': [self.lat, self.lon]
        }
        return result

    @classmethod
    def from_result(cls, result):
        """Construct this object from a result."""
        kwargs = dict(**result)
        if kwargs.get('geotag', None) is not None:
            kwargs['lat'], kwargs['lon'] = result['geotag']
        kwargs['cl_id'] = kwargs.pop('id')
        kwargs['created'] = kwargs.pop('datetime')
        kwargs['location'] = kwargs.pop('where')
        for key in list(kwargs.keys()):
            if not hasattr(cls, key):
                del kwargs[key]
        return cls(**kwargs)

    def parse_html(self, content):
        """Parse HTML content from a CL page."""
        soup = BeautifulSoup(content, 'html.parser')
        self.page = content

        # Extract geotag:
        map_tag = soup.find('div', {'id': 'map'})
        if map_tag:
            self.lat, self.lon = (float(map_tag.attrs['data-latitude']), float(map_tag.attrs['data-longitude']))

        # Extract images:
        images_div = soup.find("div", {'id': 'thumbs'})
        if images_div is not None:
            for img in images_div.find_all('a', {'class', 'thumb'}):
                url = img.attrs['href']
                if not any(url == image.url for image in self.images):
                    self.images.append(url)
        if not self.images:
            gallery_image = soup.find("div", {'class': 'gallery'})
            for img in gallery_image.find_all('img'):
                url = img.attrs['src']
                if not any(url == image.url for image in self.images):
                    self.images.append(url)
        if not self.images:
            logger.warning("No images found for {0}".format(self))
        else:
            logger.info("Added {} images to {}".format(len(self.images), self))

        # Extract text
        self.text = soup.find("section", {'id': 'postingbody'}).text

        # Extract tags
        for attrgroup in soup.find('div', {'class': 'mapAndAttrs'}).find_all('p', {'class': 'attrgroup'}):
            for attr in attrgroup.find_all('span'):
                if 'class' in attr.attrs and 'property_date' in attr['class']:
                    self.available = dt.datetime.strptime(attr['data-date'], "%Y-%m-%d").date()
                    continue

                if attr.text.endswith('ft2'):
                    try:
                        self.size = float(attr.text[:-3])
                    except ValueError:
                        logger.warning("Can't parse size tag {0}.".format(attr.text), exc_info=True)
                elif all(s in attr.text.lower() for s in ("/", "br", "ba")):
                    bedrooms, baths = attr.text.split("/", 1)
                    try:
                        self.bedrooms = int(bedrooms.lower().replace("br", "").strip())
                    except ValueError:
                        logger.warning("Can't parse bedroom tag {0}.".format(attr.text), exc_info=True)
                    try:
                        self.bathrooms = float(baths.lower().replace("ba", "").strip())
                    except ValueError:
                        logger.warning("Can't parse bathroom tag {0}.".format(attr.text), exc_info=True)
                elif not any(attr.text == tag.name for tag in self.tags):
                    self.tags.append(attr.text)


class ListingExpirationCheck(db.Model):
    __tablename__ = 'listingexpirationcheck'

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))
    listing = db.relationship("Listing", backref=db.backref("_userinfo", uselist=False))

    created = db.Column(db.DateTime)
    response_status = db.Column(db.Integer)


class CraigslistSite(db.Model):
    __tablename__ = 'clsite'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    enabled = db.Column(db.Boolean())

    def __str__(self):
        return self.name.upper()

    @property
    def url(self):
        return f'http://{self.name}.craigslist.org'

    @validates('areas')
    def validate_areas(self, key, name):
        """Validate tag lists"""
        # pylint: disable=unused-argument
        if isinstance(name, CraigslistArea):
            return name
        area = CraigslistArea.query.filter_by(name=name, site=self).one_or_none()
        if area is not None:
            return area
        area = CraigslistArea(name=name, site=self)
        db.session.add(area)
        return area


class CraigslistArea(db.Model):
    __tablename__ = 'clarea'
    id = db.Column(db.Integer(), primary_key=True)
    site_id = db.Column(db.Integer(), db.ForeignKey('clsite.id'))
    site = db.relationship('CraigslistSite', backref=db.backref('areas', uselist=True))
    name = db.Column(db.String(255))

    def __str__(self):
        return self.name.upper()


class CraigslistCategory(db.Model):
    __tablename__ = 'clcategory'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))

    def __str__(self):
        return f"{self.name.upper()}: {self.description}"

    def __repr__(self):
        return f"CraigslistCategory(name={self.name!r}, description={self.description!r})"

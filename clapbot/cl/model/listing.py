import logging
import datetime as dt

from pathlib import Path

from flask import current_app as app

from bs4 import BeautifulSoup

from sqlalchemy.orm import validates
from sqlalchemy.types import BigInteger

from . import site, image

from ...utils import coord_distance
from ...core import db

__all__ = ['tags', 'Listing', 'Tag']

logger = logging.getLogger(__name__)

tags = db.Table(
    'tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
)


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
    home_area = db.Column(db.String)

    cl_id = db.Column(BigInteger, unique=True)

    cl_site = db.Column(db.Integer(), db.ForeignKey('clsite.id'))
    site = db.relationship('site.Site', backref=db.backref("listings", uselist=True, lazy='dynamic'))
    cl_area = db.Column(db.Integer(), db.ForeignKey('clarea.id'))
    area = db.relationship('site.Area', backref=db.backref("listings", uselist=True, lazy='dynamic'))

    cl_category = db.Column(db.Integer(), db.ForeignKey('clcategory.id'))
    category = db.relationship('site.Category', backref=db.backref("listings", uselist=True, lazy='dynamic'))

    transit_stop_id = db.Column(db.Integer, db.ForeignKey("transitstop.id"))
    transit_stop = db.relationship("clapbot.model.TransitStop", backref=db.backref('listings', lazy='dynamic'))

    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    size = db.Column(db.Float)

    text = db.Column(db.Text)
    page = db.Column(db.Text)

    tags = db.relationship(Tag, secondary=tags, backref=db.backref('listings', lazy='dynamic'))
    images = db.relationship(image.Image, secondary=image.images, backref=db.backref('listings', lazy='dynamic'))

    notified = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super().__init__(**site.Area._handle_kwargs(kwargs))

    def __repr__(self):
        return f"Listing(id={self.id}, cl={self.cl_id}, site={self.site!s}, area={self.area!s})"

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
        from ...score import score_info
        return score_info(self)

    def distance_to(self, lat, lon):
        """Distance to some position."""
        return coord_distance(self.lat, self.lon, lat, lon)

    def distance_to_work(self):
        """Distance to work."""
        lat = app.config['CRAIGSLIST_SCORE_WORK_LAT']
        lon = app.config['CRAIGSLIST_SCORE_WORK_LON']
        return self.distance_to(lat, lon)

    @validates("site")
    def validate_site(self, key, value):
        """Validate a craigslist site"""
        # pylint: disable=unused-argument
        if value is not None and not isinstance(value, site.Site):
            value = site.Site.query.filter_by(name=value.lower()).one_or_none()
        if value is None:
            raise ValueError("Invalid craigslist site")
        if self.area is not None and self.area not in value.areas:
            raise ValueError(f"Invalid area, must be a member of {value}")
        return value

    @validates("area")
    def validate_area(self, key, value):
        """Validate a craigslist area"""
        # pylint: disable=unused-argument
        if not isinstance(value, site.Area):
            value = site.Area.query.filter_by(name=value.lower(), site=self.site).one_or_none()
            if value is None:
                raise ValueError("Invalid craigslist area")
        if self.site is None:
            self.site = value.site
        elif value not in self.site.areas:
            raise ValueError(f"Invalid area, must be a member of {self.site}")
        return value

    @validates("category")
    def validate_category(self, key, value):
        """Validate a craigslist site"""
        # pylint: disable=unused-argument
        if isinstance(value, site.Category):
            return value
        value = site.Category.query.filter_by(name=value.lower()).one_or_none()
        if value is None:
            raise ValueError("Invalid craigslist category")
        return value

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
        if isinstance(url, image.Image):
            return url
        img = image.Image.query.filter_by(url=url).one_or_none()
        if img is not None:
            return img
        img = image.Image(url=url)
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
            'geotag': [self.lat, self.lon],
            'site': self.site.name,
            'area': self.area.name,
            'category': self.category.name,
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

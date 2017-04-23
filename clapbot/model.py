# -*- coding: utf-8 -*-

import click
import requests
import base64
import urllib.parse
import datetime as dt
from bs4 import BeautifulSoup

from sqlalchemy.orm import validates

from .application import app, db
from .utils import coord_distance

tags = db.Table('tags', 
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
    )

images = db.Table('images', 
    db.Column('image_id', db.Integer, db.ForeignKey('image.id')),
    db.Column('listing_id', db.Integer, db.ForeignKey('listing.id')),
    )
    
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

class Image(db.Model):
    """Image belonging to a listing."""
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, unique=True)
    full = db.Column(db.LargeBinary)
    thumbnail = db.Column(db.LargeBinary)
    
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
    
    def download(self):
        """Download images."""
        response = requests.get(self.url)
        self.full = response.content
        response = requests.get(self.thumbnail_url)
        self.thumbnail = response.content
    
    @property
    def thumbnail_url(self):
        """Try to guess a thumbnail URL"""
        #: https://images.craigslist.org/00d0d_1qTvVaQpLrT_600x450.jpg
        url = urllib.parse.urlsplit(self.url)
        last_part = url.path.split("_")[-1]
        try:
            size = [int(part) for part in last_part.split("x")]
        except ValueError:
            # We don't know that the thumbnail is really valid.
            return self.url
        else:
            scheme, netloc, path, query, fragment = url
            path = self.cl_id + "_50x50c.jpg"
            return urllib.parse.urlunsplit(scheme, netloc, path, query, fragment)

class Tag(db.Model):
    """A simple craigslist tag."""
    __tablename__ = 'tag'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    
class Listing(db.Model):
    """Craigslist Listing"""
    __tablename__ = 'listing'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, unique=True)
    created = db.Column(db.DateTime)
    available = db.Column(db.Date)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    
    name = db.Column(db.String)
    price = db.Column(db.Float)
    location = db.Column(db.String)
    cl_id = db.Column(db.Integer, unique=True)
    
    area = db.Column(db.String)
    transit_stop_id = db.Column(db.Integer, db.ForeignKey("transitstop.id"))
    transit_stop = db.relationship("TransitStop", backref=db.backref('listings', lazy='dynamic'))
    
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    size = db.Column(db.Float)
    
    text = db.Column(db.Text)
    page = db.Column(db.Text)
    
    tags = db.relationship('Tag', secondary=tags,
                           backref=db.backref('listings', lazy='dynamic'))
    images = db.relationship('Image', secondary=images,
                             backref=db.backref('listings', lazy='dynamic'))
    
    notified = db.Column(db.Boolean, default=False)
    
    @property
    def transit_stop_distance(self):
        """Distance to the transit stop"""
        return coord_distance(self.lat, self.lon, self.transit_stop.lat, self.transit_stop.lon)
    
    def __repr__(self):
        """Craigslist listing repr"""
        return "<Listing cl_id={}>".format(self.cl_id)
    
    @validates("created")
    def validate_datetime(self, key, value):
        """Validate a datetime"""
        if isinstance(value, dt.datetime):
            return value
        return dt.datetime.strptime(value, "%Y-%m-%d %H:%M")
        
        
    @validates("available")
    def validate_date(self, key, value):
        """Validate a date object"""
        if isinstance(value, dt.date):
            return value
        return dt.datetime.strptime(value, "%Y-%m-%d").date()
    
    @validates('price')
    def validate_price(self, key, value):
        """Validate price."""
        if isinstance(value, float):
            return value
        return float(value.replace("$",""))
    
    @validates('images')
    def validate_images(self, key, url):
        """Validate tag lists"""
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
        if isinstance(name, Tag):
            return name
        tag = Tag.query.filter_by(name=name).one_or_none()
        if tag is not None:
            return tag
        tag = Tag(name=name)
        db.session.add(tag)
        return tag
    
    @classmethod
    def from_result(cls, result):
        """Construct this object from a result."""
        if result.get('geotag', None) is not None:
            result['lat'], result['lon'] = result['geotag']
        result['cl_id'] = result.pop('id')
        result['created'] = result.pop('datetime')
        result['location'] = result.pop('where')
        for key in list(result.keys()):
            if not hasattr(cls, key):
                del result[key]
        return cls(**result)
    
    def parse_html(self, content):
        """Parse HTML content from a CL page."""
        soup = BeautifulSoup(content, 'html.parser')
        self.page = content
        
        # Extract geotag:
        map = soup.find('div', {'id': 'map'})
        if map:
            self.lat, self.lon = (float(map.attrs['data-latitude']),
                                  float(map.attrs['data-longitude']))
        
        # Extract images:
        images = soup.find("div", {'id':'thumbs'})
        if images is not None:
            for img in images.find_all('a', {'class', 'thumb'}):
                url = img.attrs['href']
                if not any(url == image.url for image in self.images):
                    self.images.append(url)
        if not len(self.images):
            gallery_image = soup.find("div", {'class':'gallery'})
            for img in gallery_image.find_all('img'):
                url = img.attrs['src']
                if not any(url == image.url for image in self.images):
                    self.images.append(url)
        if not len(self.images):
            app.logger.warning("No images found for {0}".format(self))
            
        app.logger.info("Added {} images to {}".format(len(self.images), self))
        # Extract text
        self.text = soup.find("section", {'id':'postingbody'}).text
        
        # Extract tags
        for attrgroup in soup.find('div', {'class':'mapAndAttrs'}).find_all('p',{'class':'attrgroup'}):
            for attr in attrgroup.find_all('span'):
                if 'class' in attr.attrs and 'property_date' in attr['class']:
                    self.available = dt.datetime.strptime(attr['data-date'], "%Y-%m-%d").date()
                    continue
                
                if attr.text.endswith('ft2'):
                    try:
                        self.size = float(attr.text[:-3])
                    except ValueError:
                        app.logger.warning("Can't parse size tag {0}.".format(attr.text), exc_info=True)
                elif all(s in attr.text.lower() for s in ("/", "br", "ba")):
                    bedrooms, baths = attr.text.split("/", 1)
                    try:
                        self.bedrooms = int(bedrooms.lower().replace("br","").strip())
                    except ValueError:
                        app.logger.warning("Can't parse bedroom tag {0}.".format(attr.text), exc_info=True)
                    try:
                        self.bathrooms = int(baths.lower().replace("ba","").strip())
                    except ValueError:
                        app.logger.warning("Can't parse bathroom tag {0}.".format(attr.text), exc_info=True)
                elif not any(attr.text == tag.name for tag in self.tags):
                    self.tags.append(attr.text)
    
    def download(self):
        """Get the listing info"""
        response = requests.get(self.url)
        self.parse_html(response.content)


def init_db():
    """Initialize the database."""
    db.create_all()
    
@app.cli.command("initdb")
def init_db_command():
    """Initalize the database."""
    init_db()
    click.secho("Initialized the databse.", fg='green')
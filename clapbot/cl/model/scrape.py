import logging
import enum
import datetime as dt

from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property

from . import site
from ...core import db

__all__ = ['ScrapeStatus', 'ScrapeRecord']

logger = logging.getLogger(__name__)


class ScrapeStatus(enum.Enum):
    pending = 1
    started = 2
    finished = 3


class ScrapeRecord(db.Model):
    __tablename__ = 'scraperecord'
    id = db.Column(db.Integer(), primary_key=True)

    cl_area = db.Column(db.Integer(), db.ForeignKey('clarea.id'))
    area = db.relationship(site.Area, backref=db.backref("scrapes", uselist=True, lazy='dynamic'))

    @hybrid_property
    def site(self):
        return self.area.site

    cl_category = db.Column(db.Integer(), db.ForeignKey('clcategory.id'))
    category = db.relationship('site.Category', backref=db.backref("scrapes", uselist=True, lazy='dynamic'))

    created_at = db.Column(db.DateTime(), default=dt.datetime.now())
    scraped_at = db.Column(db.DateTime(), default=dt.datetime.now())

    status = db.Column(db.Enum(ScrapeStatus), default=ScrapeStatus.pending)
    result = db.Column(db.String(255))
    records = db.Column(db.Integer(), default=0)

    def __init__(self, **kwargs):
        super().__init__(**site.Area._handle_kwargs(kwargs))

    def __repr__(self):
        return "ScrapeRecord(id={}, stie={}, area={}, category={}, status={})".format(
            self.id, self.site.name, self.area.name, self.category.name, self.status)

    def scraper(self, filters=None, limit=None):
        from ..scrape import make_scraper
        for result in make_scraper(
                site=self.site.name, area=self.area.name, category=self.category.name, filters=filters, limit=limit):
            self.records += 1
            yield result

    def mark_celery_result(self, result):
        result.save()
        self.scraped_at = dt.datetime.now()
        self.status = ScrapeStatus.started
        self.result = result.id

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
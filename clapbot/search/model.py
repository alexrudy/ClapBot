import enum
import datetime as dt

from ..core import db


class HousingSearchStatus(enum.Enum):
    PENDING = enum.auto()
    ACTIVE = enum.auto()
    EXPIRED = enum.auto()
    DISABLED = enum.auto()


class HousingSearch(db.Model):
    __tablename__ = 'housingsearch'

    id = db.Column(db.Integer(), primary_key=True)

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship("User", backref=db.backref("housing_searches", uselist=True))

    enabled = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=dt.datetime.now)

    name = db.Column(db.String(255))
    description = db.Column(db.Text)

    target_date = db.Column(db.DateTime)
    expiration_date = db.Column(db.DateTime)

    price_min = db.Column(db.Integer())
    price_max = db.Column(db.Integer())

    require_images = db.Column(db.Boolean, default=True)

    @property
    def filters(self):
        data = {}
        if self.price_max:
            data['max_price'] = self.price_max
        if self.price_min:
            data['min_price'] = self.price_min
        if self.require_images:
            data['has_image'] = True
        return data

    @property
    def status(self):
        if not self.enabled:
            return HousingSearchStatus.DISABLED
        if self.expiration_date <= dt.datetime.now():
            return HousingSearchStatus.EXPIRED
        if self.category is None:
            return HousingSearchStatus.PENDING
        return HousingSearchStatus.ACTIVE

    cl_site = db.Column(db.Integer(), db.ForeignKey('clsite.id'))
    site = db.relationship("CraigslistSite", backref=db.backref("searches", uselist=True, lazy='dynamic'))
    cl_area = db.Column(db.Integer(), db.ForeignKey('clarea.id'))
    area = db.relationship("CraigslistArea", backref=db.backref("searches", uselist=True, lazy='dynamic'))

    cl_category = db.Column(db.Integer(), db.ForeignKey('clcategory.id'))
    category = db.relationship("CraigslistCategory", backref=db.backref("searches", uselist=True, lazy='dynamic'))

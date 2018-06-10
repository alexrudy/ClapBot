import logging

from sqlalchemy.orm import validates

from ...core import db

__all__ = ['Site', 'Area', 'Category']

logger = logging.getLogger(__name__)


class Site(db.Model):
    __tablename__ = 'clsite'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    enabled = db.Column(db.Boolean())

    def __str__(self):
        return self.name.upper()

    def __repr__(self):
        return f"Site(name={self.name.upper()}, enabled={self.enabled!r})"

    @property
    def url(self):
        return f'http://{self.name}.craigslist.org'

    @validates('areas')
    def validate_areas(self, key, name):
        """Validate tag lists"""
        # pylint: disable=unused-argument
        if isinstance(name, Area):
            return name
        area = Area.query.filter_by(name=name, site=self).one_or_none()
        if area is not None:
            return area
        area = Area(name=name, site=self)
        db.session.add(area)
        return area


class Area(db.Model):
    __tablename__ = 'clarea'
    id = db.Column(db.Integer(), primary_key=True)
    site_id = db.Column(db.Integer(), db.ForeignKey('clsite.id'))
    site = db.relationship('Site', backref=db.backref('areas', uselist=True))
    name = db.Column(db.String(255))

    def __str__(self):
        return self.name.upper()

    def __repr__(self):
        return f"Area(name={self.name.upper()!r}, site={self.stie.name.upper()!r})"

    @classmethod
    def _handle_kwargs(cls, kwargs):
        """Handle initialization kwargs"""
        if not isinstance(kwargs.get('area'), cls):
            kwargs['area'] = cls._lookup(kwargs.pop('area'), site=kwargs.pop('site', None))
        if 'site' in kwargs:
            raise ValueError("Can't pass site={site} with area={area}".format_map(kwargs))
        return kwargs

    @classmethod
    def _lookup(cls, name, site=None):
        q = cls.query.filter_by(name=name)
        if isinstance(site, Site):
            q = q.filter(cls.site_id == site.id)
        elif site is not None:
            q = q.join(Site).filter(Site.name == site)
        return q.one_or_none()


class Category(db.Model):
    __tablename__ = 'clcategory'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))

    def __str__(self):
        return f"{self.name.upper()}: {self.description}"

    def __repr__(self):
        return f"Category(name={self.name!r}, description={self.description!r})"

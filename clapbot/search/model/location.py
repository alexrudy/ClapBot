import csv
import datetime as dt

from ...core import db

boundingboxassociation = db.Table(
    'bboxes',
    db.Column('bbox_id', db.Integer, db.ForeignKey('boundingbox.id')),
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

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", backref=db.backref("bboxes", lazy='dynamic'))

    created_at = db.Column(db.DateTime, default=dt.datetime.now())

    def contains(self, lat, lon):
        """Check if this bbox contains a specific point"""
        if self.lat_min <= lat <= self.lat_max and self.lon_min <= lon <= self.lon_max:
            return True
        return False

    listings = db.relationship(
        'Listing', secondary=boundingboxassociation, backref=db.backref('bboxes', lazy='dynamic'))

    def to_csv(self, writer):
        """Write this bbox to CSV"""
        writer.writerow([self.name, self.lon_min, self.lat_min, self.lon_max, self.lat_max])


def export_bboxes(stream, bboxes):
    """Export bounding boxes to a text-stream."""
    writer = csv.writer(stream)
    for bbox in bboxes:
        bbox.to_csv(writer)


def iter_bboxes(stream):
    reader = csv.reader(stream)
    for (name, lon1, lat1, lon2, lat2) in reader:
        lat_min, lat_max = sorted([float(lat1), float(lat2)])
        lon_min, lon_max = sorted([float(lon1), float(lon2)])

        bbox = BoundingBox.query.filter_by(
            lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max).one_or_none()
        if bbox is not None:
            continue
        yield BoundingBox(name=name, lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max)

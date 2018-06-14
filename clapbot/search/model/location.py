from ...core import db


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
        """Check if this bbox contains a specific point"""
        if self.lat_min <= lat <= self.lat_max and self.lon_min <= lon <= self.lon_max:
            return True
        return False

from .utils import coord_distance

from . import db
from .model import TransitStop, BoundingBox
import pkg_resources
import csv
import io

def import_transit(agency):
    """Import transit stops for a given agency."""
    stream = io.TextIOWrapper(pkg_resources.resource_stream(__name__, 'data/transit/{}.txt'.format(agency)), encoding='utf-8')
    reader = csv.DictReader(stream)
    for row in reader:
        stop = TransitStop.query.filter_by(agency=agency, stop_id=row['stop_id']).one_or_none()
        if stop is not None:
            continue
        stop = TransitStop(agency=agency, stop_id=row['stop_id'], name=row['stop_name'], lat=row['stop_lat'], lon=row['stop_lon'])
        db.session.add(stop)
    db.session.commit()

def import_bounding_boxes(stream):
    """Import bounding boxes."""
    reader = csv.reader(stream)
    for (name, lon1, lat1, lon2, lat2) in reader:
        lat_min, lat_max = sorted([float(lat1), float(lat2)])
        lon_min, lon_max = sorted([float(lon1), float(lon2)])
        bbox = BoundingBox.query.filter_by(lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max).one_or_none()
        if bbox is not None:
            continue
        bbox = BoundingBox(name=name, lat_min=lat_min, lat_max=lat_max, lon_min=lon_min, lon_max=lon_max)
        db.session.add(bbox)
    db.session.commit()
    
def export_bounding_boxes(stream):
    """Export bounding boxes"""
    writer = csv.writer(stream)
    for bbox in BoundingBox.query:
        writer.writerow([bbox.name, bbox.lon_min, bbox.lat_min, bbox.lon_max, bbox.lat_max])


def check_inside_bboxes(listing):
    """Check that a listing is inside bboxes."""
    if listing.lat is None or listing.lon is None:
        return False
    for bbox in BoundingBox.query:
        if bbox.contains(listing.lat, listing.lon):
            return True
    else:
        return False

def find_nearest_transit_stop(listing):
    """Find the nearest transit stop to a listing."""
    if listing.lat is None or listing.lon is None:
        return
    distance = float('inf')
    closest_stop = None
    for stop in TransitStop.query.all():
        new_distance = coord_distance(listing.lat, listing.lon, stop.lat, stop.lon)
        if distance > new_distance:
            closest_stop = stop
            distance = new_distance
    listing.transit_stop = closest_stop
    
from .utils import coord_distance

from . import db
from .model import TransitStop
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
    
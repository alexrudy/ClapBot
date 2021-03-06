import datetime as dt
import logging

from flask import Blueprint, redirect
from flask import request
from celery import group

from ..core import db
from ..utils import next_url
from ..cl import model as m
from ..cl import tasks as t

from .model import HousingSearch, Status

bp = Blueprint("search.api", __name__)

logger = logging.getLogger(__name__)


def record_from_search(search):
    """Construct a search record from a housing search."""
    return m.scrape.Record(area=search.area, category=search.category)


def get_scrape_records():
    """Iterate over the scrape records for enabled housing searches."""

    # Select only areas/categories which appear in searches
    query = HousingSearch.query.filter(HousingSearch.enabled == True,
                                       HousingSearch.expiration_date >= dt.datetime.now())

    for area, category in set(
        (hs.area, hs.category) for hs in query if hs.status == Status.ACTIVE and hs.area.site.enabled):
        yield m.scrape.Record(area=area, category=category)


@bp.route('/scrape')
def scrape():
    """Launch a CL scrape"""

    tasks = []
    for record in get_scrape_records():
        db.session.add(record)
        db.session.flush()
        logger.info(f"Setting up scrape for {record}")
        tasks.append(t.scrape.s(record.id))

    db.session.commit()

    response = redirect(next_url(request))
    if not tasks:
        logger.warning("No tasks are triggered.")
    else:
        result = group(tasks).delay()
        result.save()
        response.headers['X-result-token'] = result.id

    return response


@bp.route('/scrape/<identifier>')
def scrape_single(identifier):
    """Scrape a single search object."""

    search = HousingSearch.query.get_or_404(identifier)

    if not (search.status == Status.ACTIVE and search.area.site.enabled):
        return redirect(next_url(request))

    record = record_from_search(search)
    db.session.add(record)
    db.session.flush()

    task = t.scrape.s(record.id)

    db.session.commit()

    result = task.delay()

    response = redirect(next_url(request))
    response.headers['X-result-token'] = result.id
    return response

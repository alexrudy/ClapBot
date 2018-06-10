"""
Engine behind scraping craigslist for listings and adding them to the database.
"""
import logging

from .utils import safe_iterator
# from .model import Record

# from ..search.model import HousingSearch

logger = logging.getLogger(__name__)

__all__ = ['make_scraper']


def make_scraper(site, area, category, filters=None, limit=None):
    """Make a scraper"""
    import craigslist
    filters = filters if filters is not None else {'has_image': True}
    query = craigslist.CraigslistHousing(site=site, area=area, category=category, filters=filters)
    for result in safe_iterator(query.get_results(sort_by='newest', geotagged=False, limit=limit), limit=limit):
        result['site'] = site
        result['area'] = area
        result['category'] = category
        yield result

"""
Engine behind scraping craigslist for listings and adding them to the database.
"""

import itertools

import logging

logger = logging.getLogger(__name__)

__all__ = ['iter_scraped_results']


def safe_iterator(iterable, limit):
    """Safe iterator, which just logs problematic entries."""
    iterator = itertools.islice(iterable, limit)
    while True:
        try:
            gen = next(iterator)
        except StopIteration:
            break
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(f"Exception in craigslist result: {e}")
        else:
            yield gen


def create_scraper(app, site=None, area=None):
    """Create a craigslist downloader from the settings in the app."""
    import craigslist
    site = site or app.config['CRAIGSLIST_SITE']
    area = area or app.config['CRAIGSLIST_AREA']
    return craigslist.CraigslistHousing(
        site=site,
        area=area,
        category=app.config['CRAIGSLIST_CATEGORY'],
        filters=app.config['CRAIGSLIST_FILTERS'])


def iter_scraped_results(app, site=None, area=None, limit=20):
    """Do a single scrape from craigslist and commit to the database."""
    query = create_scraper(app, site=site, area=area)
    for result in safe_iterator(
            query.get_results(sort_by='newest', geotagged=False, limit=limit),
            limit=limit):
        yield result

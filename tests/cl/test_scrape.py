import pytest

from clapbot.cl import scrape
from clapbot.cl import utils

# pylint: disable=redefined-outer-name,unused-argument


def test_save_iterator():
    def failing_iterator():
        for i in range(3):
            if i == 1:
                raise ValueError("A problem")
            yield i

    gen = utils.safe_iterator(failing_iterator(), 2)
    assert list(gen) == [0]


@pytest.fixture
def housing(monkeypatch, listing_json):
    class MockCraigslistQuery:
        def __init__(self, site, area, category, **kwargs):
            self.settings = kwargs
            self.results_kwargs = {}
            self._listings = [listing_json]
            self._i = 0

        def __iter__(self):
            return self

        def __next__(self):
            try:
                item = self._listings[self._i]
            except IndexError:
                raise StopIteration
            finally:
                self._i += 1
            if isinstance(item, Exception):
                raise item
            return item

        def get_results(self, **kwargs):
            self.results_kwargs.update(kwargs)
            return self

    monkeypatch.setattr('clapbot.cl.scrape.make_scraper', MockCraigslistQuery)


def test_iter_scraped(app, housing, nointernet, listing_json):
    with app.app_context():
        listings = list(scrape.make_scraper('sfbay', 'eby', 'apa', filters=None, limit=1))
    assert listings == [listing_json]

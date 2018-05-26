import pytest

from clapbot.cl import scrape

# pylint: disable=redefined-outer-name,unused-argument

def test_save_iterator():

    def failing_iterator():
        for i in range(3):
            if i == 1:
                raise ValueError("A problem")
            yield i

    gen = scrape.safe_iterator(failing_iterator(), 2)
    assert list(gen) == [0]

@pytest.fixture
def housing(monkeypatch, listing_json):

    class CraigslistHousing:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.results_kwargs = {}
        def get_results(self, **kwargs):
            self.results_kwargs.update(kwargs)

            while True:
                yield listing_json

    monkeypatch.setattr('craigslist.CraigslistHousing', CraigslistHousing)

def test_iter_scraped(app, housing, nointernet, listing_json):
    with app.app_context():
        listings = list(scrape.iter_scraped_results(app, limit=1))
    assert listings == [listing_json]

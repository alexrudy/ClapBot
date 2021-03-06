import json

import pytest

from celery.result import GroupResult

from clapbot.cl import tasks, model
from clapbot.core import db
# pylint: disable=unused-argument


@pytest.fixture
def scrape_record(app):
    with app.app_context():
        sr = model.scrape.Record(site='sfbay', area='eby', category='apa')
        db.session.add(sr)
        db.session.commit()
        sr_id = sr.id
    return sr_id


@pytest.mark.celery
def test_export_listing(app, celery_worker, celery_timeout, craigslist, listing, listing_json):
    """Test the task which exports a single listing to a cache file."""
    assert app.config['CRAIGSLIST_CACHE_ENABLE']

    tasks.export_listing.s(listing).delay().get(timeout=celery_timeout)

    with app.app_context():
        cache_path = model.Listing.query.get(listing).cache_path
    assert_cache_json(cache_path, listing_json)


def assert_cache_json(cache_path, listing_json):
    paths = list(cache_path.glob('*.json'))
    assert len(paths) == 1

    path = next(iter(paths))
    exported_json = json.loads(path.read_text())

    for key, value in exported_json.items():
        if isinstance(value, (int, str)):
            assert exported_json[key] == listing_json[key], f"Mismatch for {key}"


@pytest.mark.celery
def test_listing_download(app, celery_worker, celery_timeout, craigslist, listing):
    """Test the task which downloads a listing from craigslist."""
    with app.app_context():
        assert not model.Listing.query.get(listing).text

    tasks.download_listing.s(listing).delay().get(timeout=celery_timeout)

    with app.app_context():
        listing = model.Listing.query.get(listing)
        assert listing.bedrooms == 1
        assert listing.bathrooms == 1
        assert len(listing.images) == 1
        assert listing.text
        assert len(listing.tags) == 5


@pytest.mark.celery
def test_image_download(app, celery_worker, celery_timeout, craigslist, image):
    """Test the task which downloads an image from craigslist"""
    with app.app_context():
        assert model.Image.query.get(image).full is None

    tasks.download_image.s(image).delay().get(timeout=celery_timeout)

    with app.app_context():
        assert model.Image.query.get(image).full is not None


@pytest.mark.celery
def test_download_chain(app, celery_app, celery_worker, celery_timeout, craigslist, listing_json):

    with app.app_context():
        group = tasks.new_listing_pipeline(listing_json)

    result = group.delay().get(timeout=celery_timeout)
    GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)

    with app.app_context():

        listing = model.Listing.query.first()
        assert listing.bedrooms == 1
        assert listing.bathrooms == 1
        assert len(listing.images) == 1
        assert listing.text
        assert len(listing.tags) == 5

        img = model.Image.query.first()
        assert img.full is not None


@pytest.mark.celery
def test_export_all(app, celery_app, celery_worker, celery_timeout, listing, listing_json):

    result = tasks.export_listings.delay().get(timeout=celery_timeout)
    GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)

    with app.app_context():
        cache_path = model.Listing.query.get(listing).cache_path
    assert_cache_json(cache_path, listing_json)


@pytest.mark.celery
def test_ensure_download(app, celery_app, celery_worker, celery_timeout, craigslist, listing):

    result = tasks.ensure_downloaded.s(listing).delay().get(timeout=celery_timeout)
    results = GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)
    for result in results:
        GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)

    with app.app_context():

        listing = model.Listing.query.first()
        assert listing.bedrooms == 1
        assert listing.bathrooms == 1
        assert len(listing.images) == 1
        assert listing.text
        assert len(listing.tags) == 5

        img = model.Image.query.first()
        assert img.full is not None


@pytest.mark.celery
def test_scrape(app, craigslist, scrape_record, celery_app, celery_worker, celery_timeout):

    result = tasks.scrape.s(scrape_record).delay().get(timeout=celery_timeout)
    results = GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)
    for result in results:
        GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)

    with app.app_context():

        listing = model.Listing.query.first()
        assert listing.bedrooms == 1
        assert listing.bathrooms == 1
        assert len(listing.images) == 1
        assert listing.text
        assert len(listing.tags) == 5

        img = model.Image.query.first()
        assert img.full is not None

    result = tasks.scrape.s(scrape_record).delay().get(timeout=celery_timeout)
    results = GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)


@pytest.mark.celery
def test_image_download_failing(app, monkeypatch, celery_worker, celery_timeout, nointernet, image):
    """Test the task which downloads an image from craigslist"""
    with app.app_context():
        assert model.Image.query.get(image).full is None
    max_retries = 1
    monkeypatch.setattr('clapbot.cl.tasks.download_image.max_retries', max_retries)

    result = tasks.download_image.s(image).delay()
    result.get(timeout=celery_timeout, propagate=False)
    assert result.failed()
    _, count = nointernet.popitem()
    assert count == max_retries + 1


@pytest.mark.celery
def test_check_expiration(app, craigslist, scrape_record, celery_app, celery_worker, celery_timeout):

    result = tasks.scrape.s(scrape_record).delay().get(timeout=celery_timeout)
    results = GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)
    for result in results:
        GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)

    with app.app_context():
        listing_id = model.Listing.query.first().id

    status_code = tasks.check_expiration.s(listing_id).delay().get(timeout=celery_timeout)

    assert status_code == 200


@pytest.mark.celery
def test_check_expirations(app, craigslist, scrape_record, celery_app, celery_worker, celery_timeout):
    result = tasks.scrape.s(scrape_record).delay().get(timeout=celery_timeout)
    results = GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)
    for result in results:
        GroupResult.restore(result, app=celery_app).get(timeout=celery_timeout)

    result = tasks.check_expirations.s(force=True).delay().get(timeout=celery_timeout)

    result = tasks.check_expirations.delay().get(timeout=celery_timeout)


@pytest.mark.celery
def test_expire_listing(app, listing, missingpages, celery_app, celery_worker, celery_timeout):

    status_code = tasks.check_expiration.s(listing).delay().get(timeout=celery_timeout)
    assert status_code == 404

    with app.app_context():
        listing = model.Listing.query.first()

        assert listing.expired is not None

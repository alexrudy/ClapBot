# Tests for the search API
import datetime as dt
import pytest

from celery.result import AsyncResult

from clapbot.core import db
from clapbot.search.model import HousingSearch
from clapbot.search import api

# pylint: disable=unused-argument


def test_get_scrape_requests(app):
    with app.app_context():
        srs = list(api.get_scrape_records())
        assert set(record.site.name for record in srs) == set(['sfbay'])
        assert set(record.area.name for record in srs) == set(['eby'])
        assert set(record.category.name for record in srs) == set(['apa', 'hhh'])


def test_scrape(client, auth, monkeypatch):

    monkeypatch.setattr('clapbot.search.api.get_scrape_records', list)

    auth.login()
    response = client.get(f'/api/hs/v1/scrape')
    assert response.status_code == 302
    assert 'X-result-token' not in response.headers


def test_scrape_single(client, auth, monkeypatch):

    monkeypatch.setattr('clapbot.search.api.get_scrape_records', list)

    auth.login()
    response = client.get(f'/api/hs/v1/scrape/4')
    assert response.status_code == 302
    assert 'X-result-token' not in response.headers
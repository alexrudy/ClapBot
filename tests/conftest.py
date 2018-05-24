import os
import tempfile
from pathlib import Path

import pytest

from celery.contrib.testing.app import DEFAULT_TEST_CONFIG
from celery.contrib.testing import tasks

from clapbot import app as _app, db, celery

@pytest.fixture
def app(tmpdir):
    db.create_all()
    path = Path(tmpdir) / 'data' / 'cl'
    path.mkdir(parents=True, exist_ok=True)
    _app.config['CRAIGSLIST_CACHE_PATH'] = str(path)
    _app.config['CRAIGSLIST_CACHE_ENABLE'] = True
    del _app.logger.handlers[:]
    yield _app
    db.drop_all()

@pytest.fixture
def app_context(app):
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def celery_enable_logging():
    return True

@pytest.fixture
def celery_app(app):
    celery.conf.update(DEFAULT_TEST_CONFIG)
    return celery

@pytest.fixture
def celery_worker_parameters():
    return {'loglevel':'INFO'}

@pytest.fixture
def celery_timeout():
    return 10
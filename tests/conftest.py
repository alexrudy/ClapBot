from pathlib import Path

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

import pytest

from celery.contrib.testing.app import DEFAULT_TEST_CONFIG
from celery.contrib.testing import tasks    # noqa: F401 pylint: disable=unused-import

from clapbot.application import create_app
from clapbot.core import db, celery

from clapbot.users.model import User
from clapbot.users.forms import LoginForm

# pylint: disable=redefined-outer-name,unused-argument


def pytest_collection_modifyitems(session, config, items):
    """Make celery tests run last (they are slow!)"""
    for i, item in enumerate(items[:]):
        if item.get_marker("celery"):
            items.insert(-1, items.pop(i))


def run_script(engine, script):
    connection = engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.executescript(script)
        cursor.close()
        connection.commit()
    finally:
        connection.close()


@pytest.fixture
def app(tmpdir):
    app = create_app()

    with app.app_context():
        db.create_all()

        script = Path(app.config["CLAPBOT_CONFIG_DIR"]) / 'clapbot.sql'
        if script.exists():
            run_script(db.engine, script.read_text())

        path = Path(tmpdir) / 'data' / 'cl'
        path.mkdir(parents=True, exist_ok=True)
        app.config['CRAIGSLIST_CACHE_PATH'] = str(path)
        app.config['CRAIGSLIST_CACHE_ENABLE'] = True

        del app.logger.handlers[:]    # pylint: disable=no-member

    yield app

    with app.app_context():
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
    return {'loglevel': 'INFO'}


@pytest.fixture
def celery_timeout():
    return 30


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, email='test@example.com', password='test'):
        return self._client.post('/auth/login', data=dict(email=email, password=password))

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)

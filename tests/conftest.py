from pathlib import Path

import pytest

from celery.contrib.testing.app import DEFAULT_TEST_CONFIG
from celery.contrib.testing import tasks  # noqa: F401 pylint: disable=unused-import

from clapbot.application import create_app
from clapbot.core import db, celery

from clapbot.users.model import User
from clapbot.users.forms import LoginForm

# pylint: disable=redefined-outer-name,unused-argument


@pytest.fixture
def app(tmpdir):
    app = create_app()

    with app.app_context():
        db.create_all()

        path = Path(tmpdir) / 'data' / 'cl'
        path.mkdir(parents=True, exist_ok=True)
        app.config['CRAIGSLIST_CACHE_PATH'] = str(path)
        app.config['CRAIGSLIST_CACHE_ENABLE'] = True

        del app.logger.handlers[:]  # pylint: disable=no-member

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

    def login(self, email='test', password='test'):
        return self._client.post(
            '/auth/login', data=dict(email=email, password=password))

    def logout(self):
        return self._client.get('/logout')


@pytest.fixture
def auth(app, client):
    with app.app_context():
        user = User(email='test')
        user.set_password('test')
        db.session.add(user)
        db.session.commit()
    return AuthActions(client)

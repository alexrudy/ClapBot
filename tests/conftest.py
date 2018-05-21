import os
import tempfile

import pytest
from clapbot import app as _app, db

@pytest.fixture
def app():
    db.create_all()
    yield _app

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
import os
import tempfile
from pathlib import Path

import pytest
from clapbot import app as _app, db


@pytest.fixture
def app(tmpdir):
    db.create_all()
    path = Path(tmpdir) / 'data' / 'cl'
    path.mkdir(parents=True, exist_ok=True)
    _app.config['CRAIGSLIST_CACHE_PATH'] = str(path)
    yield _app

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
import time

import pytest

from celery.result import AsyncResult

from clapbot.cl import tasks

# pylint: disable=unused-argument

URL_PREFIX = '/api/cl/v1'


def test_image(client, craigslist, image):

    response = client.get(f'{URL_PREFIX}/image/{image}/full.jpg')
    assert response.status_code == 302
    assert 'images.craigslist.org' in response.headers['Location']

    response = client.get(f'{URL_PREFIX}/image/{image}/thumbnail.jpg')
    assert response.status_code == 302
    assert 'images.craigslist.org' in response.headers['Location']

    tasks.download_image(image)

    response = client.get(f'{URL_PREFIX}/image/{image}/full.jpg')
    assert response.status_code == 200

    response = client.get(f'{URL_PREFIX}/image/{image}/thumbnail.jpg')
    assert response.status_code == 200


@pytest.mark.celery
def test_scrape(client, auth, craigslist, celery_worker, celery_timeout):
    auth.login()
    response = client.get(f'{URL_PREFIX}/scrape/sfbay/eby/apa')
    assert response.status_code == 302
    result = AsyncResult(response.headers['X-result-token'])
    result.get(timeout=celery_timeout)


@pytest.mark.celery
def test_download(client, auth, craigslist, celery_worker, celery_timeout):
    auth.login()
    response = client.get(f'{URL_PREFIX}/download-all')
    assert response.status_code == 302
    result = AsyncResult(response.headers['X-result-token'])
    result.get(timeout=celery_timeout)
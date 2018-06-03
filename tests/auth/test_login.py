from werkzeug.urls import url_parse

import pytest


def test_login_flow(auth, client):

    response = client.get(f'/')
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == '/auth/login'

    auth.login()
    response = client.get(f'/')
    assert response.status_code == 200

    auth.logout()

    response = client.get(f'/')
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == '/auth/login'

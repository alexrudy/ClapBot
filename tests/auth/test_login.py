from werkzeug.urls import url_parse

from flask import url_for

import pytest


def test_login_flow(auth, client):

    response = client.get('/')
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == '/auth/login'

    auth.login()
    response = client.get('/')
    assert response.status_code == 200

    auth.logout()

    response = client.get('/')
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == '/auth/login'


def test_registration_flow(auth, client):

    response = client.get('/')
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == '/auth/login'

    response = client.get('/auth/register')
    assert response.status_code == 200

    response = client.post(
        '/auth/register',
        data={
            'username': 'other',
            'email': 'other@example.com',
            'password': 'other',
            'password2': 'other'
        })
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == '/auth/login'

    auth.login(email='other@example.com', password='other')
    response = client.get('/')
    assert response.status_code == 200

    auth.logout()

    response = client.get('/')
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == '/auth/login'

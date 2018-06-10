from werkzeug.urls import url_parse

from flask import url_for

import pytest


def assert_redirect(response, path):
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == path


def test_login_flow(auth, client):

    assert_redirect(client.get('/'), '/auth/login')
    assert b"Sign In" in client.get('/auth/login').data

    assert_redirect(auth.login(), '/')
    assert client.get('/').status_code == 200

    assert_redirect(auth.logout(), '/auth/login')
    assert_redirect(client.get('/'), '/auth/login')


def test_registration_flow(auth, client):

    assert_redirect(client.get('/'), '/auth/login')

    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Register' in response.data

    response = client.post(
        '/auth/register',
        data={
            'username': 'other',
            'email': 'other@example.com',
            'password': 'other',
            'password2': 'other'
        })
    assert_redirect(response, '/auth/login')

    response = auth.login(email='other@example.com', password='other')
    assert_redirect(response, '/')
    assert client.get('/').status_code == 200


def test_login_fail(auth):

    response = auth.login(email='test@example.com', password='wrong')
    assert_redirect(response, '/auth/login')


def test_login_unregistered(auth):

    response = auth.login(email='other@example.com', password='wrong')
    assert_redirect(response, '/auth/login')


def test_login_redirect(auth, client):

    auth.login()

    assert_redirect(client.get('/auth/login'), '/')

    assert_redirect(client.get('/auth/register'), '/')

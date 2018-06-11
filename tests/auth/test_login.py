import logging

from helpers import assert_redirect

import pytest


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


def assert_flashes(client, expected_message, expected_category='message'):
    with client.session_transaction() as session:
        try:
            category, message = session['_flashes'][0]
        except KeyError:
            raise AssertionError('nothing flashed')
        assert expected_message in message
        assert expected_category == category


@pytest.mark.parametrize(
    'data, error', [({
        'username': 'other',
        'email': 'test@example.com',
        'password': 'other',
        'password2': 'other'
    }, 'tried to register already exists'), ({
        'username': 'test',
        'email': 'other@example.com',
        'password': 'other',
        'password2': 'other'
    }, "tried to register, username already exist"), ({
        'username': 'bogus',
        'email': 'bogus@example.com',
        'password': 'other',
        'password2': 'other'
    }, 'tried to register but does not exist')],
    ids=['email-exists', 'username-exists', 'missing'])
def test_registration_fail(caplog, client, data, error):
    caplog.set_level(logging.INFO)
    assert_redirect(client.get('/'), '/auth/login')
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Register' in response.data

    response = client.post('/auth/register', data=data)
    assert response.status_code == 200
    assert b'Please use a different ' in response.data

    for record in caplog.records:
        if error in record.message:
            break
    else:
        raise AssertionError(f"Message {error!r} was never raised")


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

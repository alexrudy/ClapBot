from helpers import assert_redirect
from clapbot.users.model import User


def test_user_profile(client, auth):
    """Test that users can log in and view their profile."""

    assert_redirect(client.get('/users/profile/test'), '/auth/login')

    assert_redirect(auth.login(), '/')

    response = client.get('/users/profile/test')

    assert response.status_code == 200
    assert b'@test' in response.data

    assert client.get('/users/profile/other').status_code == 404


def test_user_model():
    user = User(
        username='test2',
        email='test2@example.com',
    )

    assert repr(user) == "User(email='test2@example.com')"

    assert user.censored_email == '***@example.com'
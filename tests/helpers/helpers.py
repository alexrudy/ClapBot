from werkzeug.urls import url_parse


def assert_redirect(response, path):
    assert response.status_code == 302
    assert url_parse(response.headers['Location']).path == path
import pytest
import datetime as dt

from helpers import assert_redirect

from clapbot.cl.model import site
from clapbot.search.model import HousingSearch


@pytest.fixture
def client(auth, client):
    auth.login()
    yield client
    auth.logout()


@pytest.fixture(params=[
    {
        'name': 'Test 1',
        'description': 'The test 1',
        'site': 'sfbay',
        'target_date': dt.date.today().strftime('%Y-%m-%d')
    },
    {
        'name': 'Test 1',
        'description': 'The test 1',
        'site': 'sfbay',
        'target_date': (dt.date.today() + dt.timedelta(days=120)).strftime('%Y-%m-%d')
    },
])
def formdata(request):
    return request.param


def test_search_crud(client, app, formdata):

    response = client.get('/search/create')
    assert response.status_code == 200
    assert b'SFBAY' in response.data

    start = dt.datetime.now()
    site_name = formdata['site']

    with app.app_context():
        s = site.Site.query.filter_by(name=formdata['site'].lower()).one_or_none()
        formdata['site'] = s.id

    client.post('/search/create', data=formdata)

    with app.app_context():
        hs = HousingSearch.query.filter_by(name=formdata['name'], description=formdata['description']).one_or_none()
        assert hs is not None, "Missing committed search result."

        assert hs.site.name == site_name
        assert hs.created_at > start
        assert hs.expiration_date < dt.datetime.now() + dt.timedelta(days=91)
        hs_id = hs.id

    response = client.get(f'/search/{hs_id}/edit')
    assert response.status_code == 200
    assert formdata['name'] in response.get_data(as_text=True)

    edit_data = {**formdata}
    edit_data['name'] = 'New Test Name'
    edit_data['price_min'] = 2000
    edit_data['price_max'] = 1000
    with app.app_context():
        s = site.Site.query.get(edit_data.pop('site'))
        edit_data['area'] = s.areas[0].id

        c = site.Category.query.first()
        edit_data['category'] = c.id

    response = client.post(f'/search/{hs_id}/edit', data=edit_data)

    assert_redirect(response, f'/users/profile/test')

    with app.app_context():
        hs = HousingSearch.query.get(hs_id)
        assert hs.price_max == 2000
        assert hs.price_min == 1000
        assert hs.name == 'New Test Name'
        assert hs.area.name in ('sfc', 'eby')
        assert hs.category.name in ('hhh', 'apa', 'swp')

    response = client.get(f'/search/{hs_id}')
    assert response.status_code == 200
    assert 'New Test Name' in response.get_data(as_text=True)

    response = client.get(f'/search/')
    assert response.status_code == 200

    response = client.delete(f'/search/{hs_id}/delete')
    assert_redirect(response, f'/users/profile/test')

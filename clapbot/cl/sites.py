from werkzeug.urls import url_parse
from bs4 import BeautifulSoup
import requests

from flask import current_app as app

from ..core import db
from .model import CraigslistSite, CraigslistArea

ALL_SITES_URL = 'http://www.craigslist.org/about/sites'


def get_all_sites():
    response = requests.get(
        ALL_SITES_URL, timeout=app.config.get("REQUESTS_TIMEOUT", 5))
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    sites = set()

    for box in soup.findAll('div', {'class': 'box'}):
        for a in box.findAll('a'):
            # Remove protocol and get subdomain
            site = url_parse(a.attrs['href']).netloc.split('.')[0]
            sites.add(site)

    for site in sites:
        obj = CraigslistSite.query.filter_by(name=site.lower()).one_or_none()
        if obj is None:
            db.session.add(CraigslistSite(name=site.lower()))
    db.session.commit()


def get_all_areas(site):
    site = CraigslistSite.query.filter_by(name=site.lower()).one_or_none()
    response = requests.get(
        site.url, timeout=app.config.get("REQUESTS_TIMEOUT", 5))
    response.raise_for_status()  # Something failed?
    soup = BeautifulSoup(response.content, 'html.parser')
    raw = soup.select('ul.sublinks li a')
    areas = set(url_parse(a.attrs['href']).path.rsplit('/')[1] for a in raw)
    for area in areas:
        obj = CraigslistArea.query.filter_by(
            name=area.lower(), site=site).one_or_none()
        if obj is None:
            db.session.add(CraigslistArea(name=area.lower(), site=site))
    db.session.commit()

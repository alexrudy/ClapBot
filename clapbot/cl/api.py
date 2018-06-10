import io

from flask import Blueprint
from flask import request, redirect, url_for, send_file

from werkzeug.urls import url_parse
from flask_login import login_required

from . import tasks as t
from . import model as m

from ..core import db
from ..utils import next_url

#: API Blueprint for craigslist
bp = Blueprint('cl.api', __name__)

# Task control buttons:
# --


@bp.route("/sites/<site>")
@login_required
def site(site):
    """Grab craigslist sites now!"""
    result = t.get_craigslist_site_info.s(site).delay()
    response = redirect(next_url(request))
    response.headers['X-result-token'] = result.id
    return response


@bp.route("/sites")
@login_required
def sites():
    """Grab craigslist sites now!"""
    result = t.get_craigslist_info.delay()
    response = redirect(next_url(request))
    response.headers['X-result-token'] = result.id
    return response


@bp.route("/scrape/<site>/<area>/<category>")
@login_required
def scrape(site, area, category):
    """Scrape craigslist now!"""
    area = m.site.Area.query.filter(m.site.Area.name == area).join(
        m.site.Area.site).filter(m.site.Site.name == site).first_or_404()

    record = m.scrape.ScrapeRecord(area=area, category=category)
    db.session.add(record)
    db.session.commit()

    result = t.scrape.s(record.id).delay()
    response = redirect(next_url(request))
    response.headers['X-result-token'] = result.id
    return response


@bp.route("/expire")
@login_required
def expire():
    """Scrape craigslist now!"""
    result = t.check_expirations.delay()
    response = redirect(next_url(request))
    response.headers['X-result-token'] = result.id
    return response


@bp.route("/download-all")
@login_required
def download_all():
    """Ensure all listings are downloaded"""
    result = t.ensure_downloaded.delay()
    response = redirect(next_url(request))
    response.headers['X-result-token'] = result.id
    return response


# Image management items
# --


@bp.route("/image/<int:identifier>/full.jpg")
def image(identifier):
    """Serve an image from the local database."""
    img = m.image.Image.query.get_or_404(identifier)
    if img.full is not None and img.full:
        return send_file(io.BytesIO(img.full), mimetype='image/jpeg')
    else:
        return redirect(img.url)


@bp.route("/image/<int:identifier>/thumbnail.jpg")
def thumbnail(identifier):
    """docstring for thumbnail"""
    img = m.image.Image.query.get_or_404(identifier)
    if img.thumbnail is not None and img.thumbnail:
        return send_file(io.BytesIO(img.thumbnail), mimetype='image/jpeg')
    else:
        return redirect(img.thumbnail_url)

import io

from flask import Blueprint
from flask import redirect, url_for, send_file

from flask_login import login_required

from . import tasks as t
from . import model as m

#: API Blueprint for craigslist
bp = Blueprint('cl.api', __name__)

# Task control buttons:
# --


@bp.route("/scrape")
@login_required
def scrape():
    """Scrape craigslist now!"""
    result = t.scrape.delay()
    response = redirect(url_for('core.home'))
    response.headers['X-result-token'] = result.id
    return response


@bp.route("/download-all")
@login_required
def download_all():
    """Ensure all listings are downloaded"""
    result = t.ensure_downloaded.delay()
    response = redirect(url_for('core.home'))
    response.headers['X-result-token'] = result.id
    return response


# Image management items
# --


@bp.route("/image/<int:identifier>/full.jpg")
def image(identifier):
    """Serve an image from the local database."""
    img = m.Image.query.get_or_404(identifier)
    if img.full is not None and img.full:
        return send_file(io.BytesIO(img.full), mimetype='image/jpeg')
    else:
        return redirect(img.url)


@bp.route("/image/<int:identifier>/thumbnail.jpg")
def thumbnail(identifier):
    """docstring for thumbnail"""
    img = m.Image.query.get_or_404(identifier)
    if img.thumbnail is not None and img.thumbnail:
        return send_file(io.BytesIO(img.thumbnail), mimetype='image/jpeg')
    else:
        return redirect(img.thumbnail_url)

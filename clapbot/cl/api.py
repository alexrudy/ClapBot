import io

from flask import Blueprint
from flask import redirect, url_for, send_file

from . import tasks as t
from . import model as m
from ..views import login_required

#: API Blueprint for craigslist
bp = Blueprint('cl.api', __name__)

# Task control buttons.


@bp.route("/scrape")
@login_required
def scrape():
    """Scrape craigslist now!"""
    t.scrape.delay()
    return redirect(url_for('home'))


@bp.route("/download-all")
@login_required
def download_all():
    """Ensure all listings are downloaded"""
    t.ensure_downloaded.delay()
    return redirect(url_for('home'))


# Image management items


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

# -*- coding: utf-8 -*-

import io
import datetime as dt
from functools import wraps
from sqlalchemy import or_
from flask import Blueprint, render_template, send_file, redirect, session, request, url_for, jsonify
from flask import current_app as app
import redis

from .core import db, bcrypt
from .model import UserListingInfo, BoundingBox
from .cl.model import Listing, Image
from . import location

bp = Blueprint('core', __name__)


def check_db():
    try:
        db.session.query("1").from_statement("SELECT 1").all()
    except:
        return False
    else:
        return True


def check_redis(url):
    r = redis.StrictRedis.from_url(url)
    try:
        r.ping()
    except:
        return False
    else:
        return True


@bp.route('/healthcheck')
def healthcheck():
    """Respond with a healthcheck"""
    info = {'time': dt.datetime.now().isoformat(), 'db': check_db()}
    if app.config['CELERY_BROKER_URL'].startswith('redis://'):
        info['redis'] = check_redis(app.config['CELERY_BROKER_URL'])
    return jsonify(info)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('token', '') != app.config['CLAPBOT_PASSWORD_TOKEN']:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/mail")
@login_required
def mailer():
    """Mail things to me!"""
    from .tasks import notify
    notify.delay()
    return redirect(url_for('home'))


@bp.route('/logout')
def logout():
    """Log the user out."""
    session.pop('token', '')
    return redirect(url_for('login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if bcrypt.check_password_hash(app.config['CLAPBOT_PASSWORD_HASH'],
                                      request.form['Password']):
            session['token'] = app.config['CLAPBOT_PASSWORD_TOKEN']
        return redirect(request.form['Redirect'])
    else:
        return render_template("login.html")


@bp.route("/latest")
@login_required
def latest():
    """Render the latest few as if they were to be emailed."""
    listings = Listing.query.order_by(Listing.created.desc()).limit(20)
    listings = filter_rejected(listings)
    listings = listings.order_by(UserListingInfo.score.desc())
    return render_template("home.html", listings=listings)


@bp.route("/")
@login_required
def home():
    """Homepage"""
    listings = Listing.query.order_by(Listing.created.desc())
    listings = filter_rejected(listings)
    listings = listings.order_by(UserListingInfo.score.desc())
    return render_template("home.html", listings=listings)


def filter_rejected(listings):
    """Filter out rejected listings"""
    joined = listings.from_self().join(UserListingInfo, isouter=True)
    return joined.filter(
        or_(~UserListingInfo.rejected, UserListingInfo.rejected == None))


@bp.route("/mobile/")
def mobile_start():
    """Mobile start page"""
    listings = Listing.query.order_by(Listing.created.desc())
    listings = filter_rejected(listings)
    listing = listings.order_by(UserListingInfo.score.desc()).first()
    return redirect(url_for("mobile", identifier=listing.id))


@bp.route("/mobile/<int:identifier>/")
def mobile(identifier):
    """A mobile view, for a single listing."""
    listing = Listing.query.get_or_404(identifier)
    prev_lisitng = Listing.query.filter(
        Listing.created < listing.created).order_by(Listing.created.desc())
    prev_lisitng = prev_lisitng.limit(1).one_or_none()
    next_lisitng = Listing.query.filter(
        Listing.created > listing.created).order_by(Listing.created.asc())
    next_lisitng = next_lisitng.limit(1).one_or_none()
    return render_template(
        "mobile.html",
        listing=listing,
        previous_listing=prev_lisitng,
        next_listing=next_lisitng)


@bp.route("/mobile/starred/")
def mobile_starred(identifier):
    """Mobile starred items"""
    joined = listings.from_self().join(UserListingInfo, isouter=True)
    return joined.filter(
        or_(~UserListingInfo.rejected, UserListingInfo.rejected == None))


@bp.route("/image/<int:identifier>/full.jpg")
def image(identifier):
    """Serve an image from the local database."""
    img = Image.query.get_or_404(identifier)
    if img.full is not None:
        return send_file(io.BytesIO(img.full), mimetype='image/jpeg')
    else:
        return redirect(img.url)


@bp.route("/image/<int:identifier>/thumbnail.jpg")
def thumbnail(identifier):
    """docstring for thumbnail"""
    img = Image.query.get_or_404(identifier)
    if img.thumbnail is not None and len(img.thumbnail):
        return send_file(io.BytesIO(img.thumbnail), mimetype='image/jpeg')
    else:
        return redirect(img.thumbnail_url)


@bp.route("/listing/starred")
@login_required
def starred():
    """Starred lisitngs"""
    listings = Listing.query.order_by(Listing.created.desc())
    listings = listings.from_self().join(
        UserListingInfo, isouter=True).filter(
            or_(~UserListingInfo.rejected, UserListingInfo.rejected == None),
            UserListingInfo.starred == True)
    listings = listings.order_by(UserListingInfo.score.desc())
    return render_template("home.html", listings=listings, title='Starred')


@bp.route("/listing/<int:id>/star", methods=['POST'])
@login_required
def star(id):
    """Star the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.starred = not listing.userinfo.starred
    db.session.commit()
    return jsonify({'id': id, 'starred': listing.userinfo.starred})


@bp.route("/listing/<int:id>/reject", methods=['POST'])
@login_required
def reject(id):
    """Reject the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.rejected = not listing.userinfo.rejected
    db.session.commit()
    return jsonify({'id': id, 'rejected': listing.userinfo.rejected})


@bp.route("/listing/<int:id>/upvote", methods=['POST'])
@login_required
def upvote(id):
    """Reject the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.score += 100
    db.session.commit()
    return jsonify({'id': id, 'score': listing.userinfo.score})


@bp.route("/listing/<int:id>/downvote", methods=['POST'])
@login_required
def downvote(id):
    """Reject the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.score -= 100
    db.session.commit()
    return jsonify({'id': id, 'score': listing.userinfo.score})


@bp.route("/listing/<int:id>/", methods=['GET', 'POST'])
@login_required
def listing(id):
    """View a single listing."""
    listing = Listing.query.get_or_404(id)
    if request.method == 'POST':
        listing.userinfo.rejected = request.form.get('rejected', False)
        listing.userinfo.contacted = request.form.get('contacted', False)
        listing.userinfo.notes = request.form['notes']
        db.session.commit()
        return redirect(url_for('listing', id=id))
    return render_template("single.html", listing=listing)


@bp.route("/bboxes/", methods=['POST'])
@login_required
def bboxes():
    """Update the bounding boxes."""
    if request.method == 'POST':
        bboxes = io.StringIO(request.form.get('bboxes', ''))
        BoundingBox.query.delete()
        location.import_bounding_boxes(bboxes)
    return redirect(url_for('settings'))


@bp.route("/settings/")
@login_required
def settings():
    """Settings view"""
    email = app.config['MAIL_DEFAULT_RECIPIENTS']
    craigslist = {
        key[len('CRAIGSLIST_'):]: value
        for key, value in app.config.items() if key.startswith('CRAIGSLIST_')
    }
    scoring = {
        key.replace("CRAIGSLIST_", '').replace('SCORE_', ''): value
        for key, value in app.config.items()
        if key.startswith('SCORE_') or key.startswith('CRAIGSLIST_SCORE_')
    }

    stream = io.StringIO()
    location.export_bounding_boxes(stream)

    return render_template(
        "settings.html",
        email=email,
        craigslist=craigslist,
        scoring=scoring,
        bboxes=stream.getvalue())

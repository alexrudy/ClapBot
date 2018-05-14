# -*- coding: utf-8 -*-

import io
import datetime as dt
from functools import wraps
from sqlalchemy import or_
from flask import render_template, send_file, redirect, session, request, g, url_for, jsonify

from .application import app, db, bcrypt
from .model import Listing, Image, UserListingInfo

from .tasks import notify, scraper

import redis

def check_db():
    try:
        db.session.query("1").from_statement("SELECT 1").all()
        return True
    except:
        return False
        
def check_redis(url):
    r = redis.StrictRedis.from_url(url)
    try:
        r.ping()
    except:
        return False
    else:
        return True

@app.route('/healthcheck')
def healthcheck():
    """Respond with a healthcheck"""
    info = {'time': dt.datetime.now().isoformat(), 'db': check_db()}
    if app.config['CELERY_BROKER_URL'].startswith('redis://'):
        info['redis'] = check_redis(app.config['CELERY_BROKER_URL'])
    return jsonify(info)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('token','') != app.config['CLAPBOT_PASSWORD_TOKEN']:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/mail")
@login_required
def mailer():
    """Mail things to me!"""
    notify.delay()
    return redirect(url_for('home'))

@app.route("/scrape")
@login_required
def scrape():
    """Scrape craigslist now!"""
    scraper.delay()
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    """Log the user out."""
    session.pop('token','')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if bcrypt.check_password_hash(app.config['CLAPBOT_PASSWORD_HASH'], request.form['Password']):
            session['token'] = app.config['CLAPBOT_PASSWORD_TOKEN']
        return redirect(request.form['Redirect'])
    else:
        return render_template("login.html")

@app.route("/latest")
@login_required
def latest():
    """Render the latest few as if they were to be emailed."""
    listings = Listing.query.order_by(Listing.created.desc()).limit(20)
    listings = filter_rejected(listings)
    listings = listings.order_by(UserListingInfo.score.desc())
    return render_template("home.html", listings=listings)

@app.route("/")
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
    return joined.filter(or_(~UserListingInfo.rejected,UserListingInfo.rejected == None))

@app.route("/mobile/")
def mobile_start():
    """Mobile start page"""
    listings = Listing.query.order_by(Listing.created.desc())
    listings = filter_rejected(listings)
    listing = listings.order_by(UserListingInfo.score.desc()).first()
    return redirect(url_for("mobile", identifier=listing.id))

@app.route("/mobile/<int:identifier>/")
def mobile(identifier):
    """A mobile view, for a single listing."""
    listing = Listing.query.get_or_404(identifier)
    prev_lisitng = Listing.query.filter(Listing.created < listing.created).order_by(Listing.created.desc())
    prev_lisitng = prev_lisitng.limit(1).one_or_none()
    next_lisitng = Listing.query.filter(Listing.created > listing.created).order_by(Listing.created.asc())
    next_lisitng = next_lisitng.limit(1).one_or_none()
    return render_template("mobile.html", listing=listing, previous_listing=prev_lisitng, next_listing=next_lisitng)

@app.route("/mobile/starred/")
def mobile_starred(identifier):
    """Mobile starred items"""
    joined = listings.from_self().join(UserListingInfo, isouter=True)
    return joined.filter(or_(~UserListingInfo.rejected,UserListingInfo.rejected == None))

@app.route("/image/<int:identifier>/full.jpg")
def image(identifier):
    """Serve an image from the local database."""
    img = Image.query.get_or_404(identifier)
    if img.full is not None:
        return send_file(io.BytesIO(img.full), mimetype='image/jpeg')
    else:
        return redirect(img.url)

@app.route("/image/<int:identifier>/thumbnail.jpg")
def thumbnail(identifier):
    """docstring for thumbnail"""
    img = Image.query.get_or_404(identifier)
    if img.thumbnail is not None:
        return send_file(io.BytesIO(img.thumbnail), mimetype='image/jpeg')
    else:
        return redirect(img.thumbnail_url)
    

@app.route("/listing/starred")
@login_required
def starred():
    """Starred lisitngs"""
    listings = Listing.query.order_by(Listing.created.desc())
    listings = listings.from_self().join(UserListingInfo, isouter=True).filter(or_(~UserListingInfo.rejected,UserListingInfo.rejected == None), UserListingInfo.starred == True)
    listings = listings.order_by(UserListingInfo.score.desc())
    return render_template("home.html", listings=listings, title='Starred')

@app.route("/listing/<int:id>/star", methods=['POST'])
@login_required
def star(id):
    """Star the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.starred = not listing.userinfo.starred
    db.session.commit()
    return jsonify({'id':id, 'starred': listing.userinfo.starred})

@app.route("/listing/<int:id>/reject", methods=['POST'])
@login_required
def reject(id):
    """Reject the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.rejected = not listing.userinfo.rejected
    db.session.commit()
    return jsonify({'id':id, 'rejected': listing.userinfo.rejected })
    
@app.route("/listing/<int:id>/upvote", methods=['POST'])
@login_required
def upvote(id):
    """Reject the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.score += 100
    db.session.commit()
    return jsonify({'id':id,'score':listing.userinfo.score})

@app.route("/listing/<int:id>/downvote", methods=['POST'])
@login_required
def downvote(id):
    """Reject the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.score -= 100
    db.session.commit()
    return jsonify({'id':id,'score':listing.userinfo.score})

@app.route("/listing/<int:id>/", methods=['GET', 'POST'])
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

@app.route("/listing/clid/<int:clid>/")
@login_required
def listing_cragislistid():
    """View a listing by craigslist ID"""
    pass

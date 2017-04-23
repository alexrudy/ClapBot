# -*- coding: utf-8 -*-

import io
from functools import wraps
from flask import render_template, send_file, redirect, session, request, g, url_for

from .application import app, db, bcrypt
from .model import Listing, Image

from .tasks import notify

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('token','') != app.config['CLAPBOT_PASSWORD_TOKEN']:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/mail/")
@login_required
def mailer():
    """Mail things to me!"""
    notify.delay()
    return redirect(url_for('home'))
    

@app.route('/logout')
def logout():
    """Log the user out."""
    session.pop('token','')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #TODO: Handle passwords:
        print("Checking password {0}".format(request.form['Password']))
        if bcrypt.check_password_hash(app.config['CLAPBOT_PASSWORD_HASH'], request.form['Password']):
            session['token'] = app.config['CLAPBOT_PASSWORD_TOKEN']
        return redirect(url_for('home'))
    else:
        return render_template("login.html")

@app.route("/latest/")
@login_required
def latest():
    """Render the latest few as if they were to be emailed."""
    listings = Listing.query.order_by(Listing.created.desc()).limit(20)
    return render_template("notify.html", listings=listings)

@app.route("/")
@login_required
def home():
    """Homepage"""
    listings = Listing.query.filter(Listing.transit_stop_id != None).order_by(Listing.created.desc())
    return render_template("home.html", listings=listings)

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
    

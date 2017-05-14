# -*- coding: utf-8 -*-

import io
from functools import wraps
from sqlalchemy import or_
from flask import render_template, send_file, redirect, session, request, g, url_for, jsonify

from .application import app, db, bcrypt
from .model import Listing, Image, UserListingInfo

from .tasks import notify

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
    listings = listings.from_self().join(UserListingInfo, isouter=True).filter(or_(~UserListingInfo.rejected,UserListingInfo.rejected == None))
    listings = listings.order_by(UserListingInfo.score.desc())
    return render_template("home.html", listings=listings)

@app.route("/")
@login_required
def home():
    """Homepage"""
    listings = Listing.query.filter(Listing.transit_stop_id != None)
    listings = listings.order_by(Listing.created.desc())
    listings = listings.from_self().join(UserListingInfo, isouter=True).filter(or_(~UserListingInfo.rejected,UserListingInfo.rejected == None))
    listings = listings.order_by(UserListingInfo.score.desc())
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
    

@app.route("/listing/<int:id>/reject", methods=['POST'])
@login_required
def reject(id):
    """Reject the named listing."""
    listing = Listing.query.get_or_404(id)
    listing.userinfo.rejected = True
    db.session.commit()
    return jsonify({'id':id,'score':listing.userinfo.score})
    
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
        print(list(request.form.keys()))
        listing.userinfo.rejected = request.form.get('rejected', False)
        listing.userinfo.contacted = request.form.get('contacted', False)
        listing.userinfo.notes = request.form['notes']
        db.session.commit()
        return redirect(url_for('listing', id=id))
    return render_template("single.html", listing=listing)

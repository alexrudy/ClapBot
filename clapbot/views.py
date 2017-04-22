# -*- coding: utf-8 -*-

import io
from flask import render_template, send_file, redirect

from .application import app, db
from .model import Listing, Image

from .notify import send_notification

@app.route("/mail/")
def mailer():
    """Mail things to me!"""
    listings = Listing.query.order_by(Listing.created).filter_by(notified=False).limit(20).all()
    send_notification(listings)
    return redirect("/")
    

@app.route("/latest/")
def latest():
    """Render the latest few as if they were to be emailed."""
    listings = Listing.query.order_by(Listing.created).limit(20)
    return render_template("notify.html", listings=listings)

@app.route("/")
def home():
    """Homepage"""
    listings = Listing.query.order_by(Listing.created)
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
    

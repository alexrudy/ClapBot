# -*- coding: utf-8 -*-

from flask_mail import Message
from flask import render_template
from .application import app, mail, db

def send_notification(listings):
    """docstring for send_notification"""
    n = len(listings)
    msg = Message(f"ClapBot's latest {n:d} listings",
                      recipients=app.config['MAIL_DEFAULT_RECIPIENTS'])
    msg.text = f"ClapBot's latest {n:d} listings"
    msg.html = render_template("notify.html", listings=listings)
    mail.send(msg)
    
    for listing in listings:
        listing.notified = True
    db.session.commit()
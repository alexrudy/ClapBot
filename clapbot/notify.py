# -*- coding: utf-8 -*-

from flask_mail import Message
from flask import render_template
from .application import app, mail, db

def send_notification(listings):
    """docstring for send_notification"""
    n = len(listings)
    msg = Message("ClapBot's latest {n:d} listings".format(n),
                      recipients=app.config['MAIL_DEFAULT_RECIPIENTS'])
    msg.text = "ClapBot's latest {n:d} listings".format(n)
    msg.html = render_template("notify.html", listings=listings)
    mail.send(msg)
    
    for listing in listings:
        listing.notified = True
    db.session.commit()
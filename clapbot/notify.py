# -*- coding: utf-8 -*-

from flask_mail import Message
from flask import render_template, current_app
from .application import mail


def send_notification(listings):
    """Send a mail notification about some listings"""
    n = len(listings)
    msg = Message(
        "ClapBot's latest {n:d} listings".format(n=n),
        recipients=current_app.config['MAIL_DEFAULT_RECIPIENTS'])
    msg.text = "ClapBot's latest {n:d} listings".format(n=n)
    msg.html = render_template("notify.html", listings=listings)
    mail.send(msg)

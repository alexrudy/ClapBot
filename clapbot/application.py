# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_scss import Scss
from flask_mail import Mail
from celery import Celery
import logging
import socket
from pathlib import Path

# logging.basicConfig(format='--> %(levelname)-8s: %(message)s', level=logging.DEBUG)

def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


app = Flask('clapbot')
del app.logger.handlers[:]
app.logger.propogate = True
app.config.from_object('clapbot.defaults')
if os.environ.get('CLAPBOT_SETTINGS', ''):
    app.config.from_envvar('CLAPBOT_SETTINGS')
    app.logger.info(f"Loaded configuration from CLAPBOT_SETTINGS={os.environ['CLAPBOT_SETTINGS']}")
if os.environ.get('CLAPBOT_ENVIRON', ''):
    path = Path.cwd() / 'config' / os.environ['CLAPBOT_ENVIRON'] / 'clapbot.cfg'
    if path.exists():
        app.config.from_pyfile(str(path))
        app.logger.info(f"Loaded configuration from {path!s} via CLAPBOT_ENVIRON")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
scss = Scss(app)
bcrypt = Bcrypt(app)
app.config['CLAPBOT_PASSWORD_HASH'] = bcrypt.generate_password_hash(app.config.pop('CLAPBOT_PASSWORD'))

celery = make_celery(app)

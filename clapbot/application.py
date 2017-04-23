# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_scss import Scss
from flask_mail import Mail
from celery import Celery
import logging

logging.basicConfig(format='--> %(levelname)-8s: %(message)s', level=logging.DEBUG)

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
app.config.from_pyfile(os.path.abspath('clapbot_config.py'))
db = SQLAlchemy(app)
mail = Mail(app)
Scss(app)
celery = make_celery(app)

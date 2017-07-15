# -*- coding: utf-8 -*-
import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_scss import Scss
from flask_mail import Mail
from celery import Celery
import logging
import socket

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


instance_dir = os.getcwd()
if 'CLAPBOT_INSTANCE' in os.environ:
    instance_dir = os.path.abspath(os.path.expanduser(os.environ['CLAPBOT_INSTANCE']))
if 'VIRTUAL_ENV' in os.environ:
    if os.path.isfile(os.path.join(os.environ['VIRTUAL_ENV'], '.project')):
        project_dir = os.path.abspath(os.path.expanduser(open(os.path.join(os.environ['VIRTUAL_ENV'], '.project')).read().strip('\r\n')))
        instance_candidate = os.path.join(project_dir, 'config', 'develop')
        if os.path.isdir(instance_candidate):
            instance_dir = os.path.join(project_dir, 'config', 'develop')
    


app = Flask('clapbot', instance_path=instance_dir, instance_relative_config=True)
del app.logger.handlers[:]
app.logger.propogate = True
app.config.from_object('clapbot.defaults')
app.config.from_envvar('CLAPBOT_SETTINGS')
db = SQLAlchemy(app)
mail = Mail(app)
scss = Scss(app)
bcrypt = Bcrypt(app)
app.config['CLAPBOT_PASSWORD_HASH'] = bcrypt.generate_password_hash(app.config.pop('CLAPBOT_PASSWORD'))

celery = make_celery(app)

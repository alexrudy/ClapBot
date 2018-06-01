# -*- coding: utf-8 -*-
import os
from pathlib import Path

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_scss import Scss
from flask_mail import Mail
from flask_login import LoginManager
from celery import Celery

db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
migrate = Migrate()
login = LoginManager()


def create_celery_app():
    capp = Celery('clapbot')

    TaskBase = capp.Task

    class ContextTask(TaskBase):
        abstract = True
        flask_app = None

        def __call__(self, *args, **kwargs):
            with self.flask_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    capp.Task = ContextTask
    return capp


celery = create_celery_app()


def init_celery_app(app, celery):
    celery.conf.update({
        key[len("CELERY_"):].lower(): value
        for key, value in app.config.items()
    })
    celery.Task.flask_app = app


def create_app():
    app = Flask('clapbot')
    del app.logger.handlers[:]
    app.logger.propogate = True
    app.config.from_object('clapbot.defaults')

    if os.environ.get('CLAPBOT_SETTINGS', ''):
        app.config.from_envvar('CLAPBOT_SETTINGS')
        app.logger.info(
            f"Loaded configuration from CLAPBOT_SETTINGS={os.environ['CLAPBOT_SETTINGS']}"
        )

    if os.environ.get('CLAPBOT_ENVIRON', ''):
        path = Path.cwd(
        ) / 'config' / os.environ['CLAPBOT_ENVIRON'] / 'clapbot.cfg'
        if path.exists():
            app.config.from_pyfile(str(path))
            app.logger.info(
                f"Loaded configuration from {path!s} via CLAPBOT_ENVIRON")

    db.init_app(app)
    init_celery_app(app, celery)
    migrate.init_app(app)
    mail.init_app(app)
    Scss(app)
    login.init_app(app)
    bcrypt.init_app(app)
    app.config['CLAPBOT_PASSWORD_HASH'] = bcrypt.generate_password_hash(
        app.config.pop('CLAPBOT_PASSWORD'))

    from .views import bp as core_bp
    app.register_blueprint(core_bp)

    from .cl.api import bp as cl_api_bp
    app.register_blueprint(cl_api_bp, url_prefix='/cl/api/v1/')

    return app

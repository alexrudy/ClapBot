# -*- coding: utf-8 -*-

from .application import app, celery, db
from . import model
from . import scrape
from . import views
from . import tasks
from . import cli
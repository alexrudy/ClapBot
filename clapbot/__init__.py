# -*- coding: utf-8 -*-
import warnings
from . import views  # noqa: F401

warnings.filterwarnings(
    'ignore',
    module='psycopg2',
    message='The psycopg2 wheel package will be renamed from release')

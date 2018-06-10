# -*- coding: utf-8 -*-
import math

from flask import url_for
from werkzeug.urls import url_parse


def coord_distance(lat1, lon1, lat2, lon2):
    """Finds the distance between two pairs of latitude and longitude."""
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km


def next_url(request, default='core.home'):
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for(default)
    return next_page

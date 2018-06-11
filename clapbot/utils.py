# -*- coding: utf-8 -*-
import math

from flask import url_for, redirect, request
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
    """Construct a URL from an optional *next* parameter to the url, with a default endpoint."""
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for(default)
    return next_page


def redirect_result(result, endpoint='core.home'):
    """Redirect to the *next* URL, and add the result identifier to the response."""
    response = redirect(next_url(request, default=endpoint))

    result.save()
    response.headers['X-result-token'] = result.id

    return response

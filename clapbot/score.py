# -*- coding: utf-8 -*-
"""
Score listings
"""
from .application import app
import datetime as dt

_scorefuncs = set()

def scorer(f):
    """Decorator marking as a score function."""
    _scorefuncs.add(f)
    return f

def score_info(listing):
    """Return scoring information."""
    info = {}
    for sf in _scorefuncs:
        info[sf.__name__] = float(sf(listing))
    return info

def score_all(listing):
    """docstring for score_all"""
    listing.userinfo.score = sum(float(sf(listing)) for sf in _scorefuncs)
    
@scorer
def age(listing):
    """Score against listing age."""
    listing_age = abs((dt.date.today() - listing.created.date()).days)
    if listing_age < 1:
        return 20
    elif listing_age < 4:
        return 0
    elif listing_age < 7:
        return -20
    else:
        return -3000

@scorer
def transit(listing):
    """Score a listing's transit options."""
    if listing.transit_stop is None:
        return -200
    elif listing.transit_stop_distance < 1.0:
        return 500
    elif listing.transit_stop_distance < 1.5:
        return (2.0 - listing.transit_stop_distance) * 500
    elif listing.transit_stop_distance < 3.0:
        return (3.0 - listing.transit_stop_distance) * 100
    else:
        return 0

@scorer
def location(listing):
    """Score location"""
    if listing.lat is None:
        return 0.0
    to_berk = listing.distance_to(37.876685, -122.261998)
    if to_berk < 10.0:
        return 1000 * ((10.0 - to_berk) / 10.0)
    elif to_berk < 20.0:
        return 250 * ((20.0 - to_berk) / 20.0)
    return 0.0

@scorer
def title(listing):
    """Suspicious title scoring."""
    if "studio" in listing.name.lower():
        return -1500
    return 0.0

@scorer
def pictures(listing):
    """Score by number of images."""
    nimages = len(listing.images)
    if nimages == 0:
        return -500
    elif nimages == 1:
        return -200
    elif nimages < 4:
        return 0
    else:
        return 200

@scorer
def tags(listing):
    """Score tags"""
    score = 0.0
    if any("w/d in unit" == tag.name for tag in listing.tags):
        score += 500
    elif any("laundry on site" == tag.name for tag in listing.tags):
        score += 150
    elif any("laundry in bldg" == tag.name for tag in listing.tags):
        score += 150
    elif any("w/d hookups" == tag.name for tag in listing.tags):
        score += 150
    elif any("no laundry on site" == tag.name for tag in listing.tags):
        score -= 300
    
    if any("furnished" == tag.name for tag in listing.tags):
        score -= 250
    
    if any("no smoking" == tag.name for tag in listing.tags):
        score += 100
    
    if any("house" == tag.name for tag in listing.tags):
        score += 300
    elif any("condo" == tag.name for tag in listing.tags):
        score += 150
    elif any("apartment" == tag.name for tag in listing.tags):
        score += 5
    return score

@scorer
def availability(listing):
    """Score based on availability date."""
    if listing.available is None:
        return -500
    target = dt.datetime.strptime(app.config['SCORE_TARGET_DATE'], '%Y-%m-%d').date()
    delta = (target - listing.available).days
    multiplier = 0.5
    if listing.available < listing.created.date():
        multiplier = 0.2
    if delta > 32:
        return -0.5 * multiplier * (listing.price/30.0) * delta
    elif delta > 0:
        return -0.1 * multiplier * (listing.price/30.0) * delta
    elif delta < 0:
        return -0.25 * multiplier * 2000.0/3.0 * abs(delta)
    return 0.0
    
@scorer
def bd_ba(listing):
    """Score based on number of bedrooms."""
    score = 0.0
    if listing.bedrooms is None:
        return score
    size = listing.size if listing.size is not None else 250 * listing.bedrooms
    bathrooms = 1.5 if listing.bathrooms is None else listing.bathrooms
    if bathrooms > 2 and bathrooms > listing.bedrooms:
        score += -3000
    
    score += min(listing.bedrooms,3) * 500 + 0.75 * size + min(bathrooms,3) * 250 
    return score

@scorer
def price(listing):
    """Score based on number of bedrooms."""
    if listing.price is None:
        return -4000
    score = 0.0
    bedrooms = 1.0 if listing.bedrooms is None else listing.bedrooms
    if (bedrooms * 1000.0) > listing.price:
        score += -1000 - ((bedrooms * 750.0)/listing.price - 1.0) * 1000
    
    return -1.0 * listing.price + score
# -*- coding: utf-8 -*-

from .application import app, db
from . import scrape
from .model import Listing
from . import tasks
from . import location

import os
import io
import glob
import json

import pkg_resources
from tqdm import tqdm
import click
import celery
import time

def celery_progress(resultset):
    """A progress bar for a celery group."""
    with tqdm(len(resultset)) as pbar:
        pbar.update(0)
        while not resultset.ready():
            pbar.update(sum(int(result.ready()) for result in resultset))
            time.sleep(0.1)
        pbar.update(sum(int(result.ready()) for result in resultset))
    return

@app.cli.command("download")
@click.option("--save/--no-save", help="Save files?")
@click.option("--force/--no-force", help="Force ingest?")
@click.option("--images/--no-images", help="Download Images?")
def download_command(save, force, images):
    """Download extra craigslist information from a listing."""
    if force:
        q = Listing.query
    else:
        q = Listing.query.filter_by(text=None)
    n = q.count()
    click.echo("Downloading Craigslist page for {n:d} listings.".format(n=n))
    if images:
        group = celery.group([celery.chain(
                                          tasks.download.si(listing.id), 
                                          tasks.download_images.si(listing.id, save=save, force=force)) 
                             for listing in q])
    else:
        group = celery.group([tasks.download.si(listing.id, save=save) for listing in q])
    result = group()

@app.cli.command("score")
def score_command():
    """Score listings"""
    q = Listing.query
    n = q.count()
    click.echo("Adding location info for {n:d} listings.".format(n=n))
    group = celery.group([tasks.score.si(listing.id) for listing in q])
    group()

@app.cli.command("locate")
def locate_command():
    """Add location info to listings."""
    q = Listing.query
    n = q.count()
    click.echo("Adding location info for {n:d} listings.".format(n=n))
    group = celery.group([tasks.location_info.si(listing.id) for listing in q])
    result = group()
    
@app.cli.command("scrape")
@click.option("--limit", type=int, default=app.config['CRAIGSLIST_MAX_SCRAPE'], help="Limit the number of scraped results.")
@click.option("--to-json / --no-to-json", help="Dump the data to a JSON file.")
def scrape_command(limit, to_json=False):
    """CLI Interface for scraping."""
    click.echo("Scraping {0:d} items.".format(limit))
    if to_json:
        path = os.path.join(app.instance_path, app.config['CRAIGSLIST_CACHE_PATH'])
        scrape.scrape_to_json(path, limit=limit)
    else:
        scrape.scrape(db.session, limit=limit)

@app.cli.command("ingest")
@click.option("--path", default=app.config['CRAIGSLIST_CACHE_PATH'], type=click.Path(exists=True), help="Path to import entries to db.")
def ingest_command(path):
    """Injest JSON files at the given path into the database."""
    for filename in glob.iglob(os.path.join(path, '*.json')):
        scrape.ingest_result(db.session, json.load(open(filename)))
    db.session.commit()
    
    for filename in pkg_resources.resource_listdir(__name__, "data/transit/"):
        agency, ext = os.path.splitext(os.path.basename(filename))
        click.echo("ingesting transit from {}".format(agency))
        location.import_transit(agency)
    
    stream = io.TextIOWrapper(pkg_resources.resource_stream(__name__, "data/boxes.csv"))
    location.import_bounding_boxes(stream)
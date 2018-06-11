import datetime as dt

from flask import Blueprint, render_template, current_app
from flask import redirect, url_for, flash

from flask_login import current_user, login_required

from sqlalchemy import or_

from ..core import db
from ..cl.model import Listing, scrape
from .model import HousingSearch
from .forms import HousingSearchCreate, HousingSearchEditForm

bp = Blueprint('search', __name__)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():

    form = HousingSearchCreate()
    if form.validate_on_submit():
        if len(current_user.housing_searches) > current_app.config['CRAIGSLIST_MAX_USER_SEARCHES']:
            flash(f"{current_user.username} has exceeded maximum searches")
            return redirect(url_for('user.profile', username=current_user.username))

        hs = HousingSearch(
            name=form.name.data,
            description=form.description.data,
            target_date=dt.datetime.combine(form.target_date.data, dt.time(0, 0, 0)),
            created_at=dt.datetime.now(),
            site=form.site.data,
            owner=current_user)

        if any((uhs.cl_site == hs.cl_site) and (uhs.cl_area == hs.cl_area) for uhs in current_user.housing_searches):
            flash(f"{current_user.username} already has an active search for {hs.cl_site}/{hs.cl_area}")

        expires = hs.target_date + dt.timedelta(days=30)
        if (expires - dt.datetime.now()) > dt.timedelta(days=90):
            expires = dt.datetime.now() + dt.timedelta(days=90)

        hs.expiration_date = expires
        db.session.add(hs)
        db.session.commit()
        current_app.logger.info("Created a new search setting.")
        return redirect(url_for('user.profile', username=current_user.username))

    return render_template('search/new.html', form=form)


@bp.route('/<identifier>/delete', methods=['GET', 'POST'])
@login_required
def delete(identifier):
    hs = HousingSearch.query.get_or_404(identifier)

    db.session.delete(hs)
    db.session.commit()
    return redirect(url_for('user.profile', username=current_user.username))


@bp.route('/<identifier>/edit', methods=['GET', 'POST'])
@login_required
def edit(identifier):
    hs = HousingSearch.query.get_or_404(identifier)

    form = HousingSearchEditForm(obj=hs)

    if form.validate_on_submit():
        form.populate_obj(hs)

        if hs.price_min > hs.price_max:
            hs.price_min, hs.price_max = hs.price_max, hs.price_min

        db.session.commit()
        return redirect(url_for('user.profile', username=current_user.username))

    return render_template('search/edit.html', form=form, search=hs)


@bp.route('/<identifier>')
@login_required
def view(identifier):
    """View the results of a single search"""

    hs = HousingSearch.query.get_or_404(identifier)
    listings = Listing.query.filter(hs.query_predicate()).order_by(Listing.created.desc())

    record = scrape.Record.query.filter(scrape.Record.area == hs.area, scrape.Record.category == hs.category).order_by(
        scrape.Record.created_at, scrape.Record.status != scrape.Status.pending).first()

    return render_template('search/view.html', search=hs, listings=listings, record=record)


@bp.route('/')
@login_required
def home():
    """Home page view, with results from all searches."""

    predicates = []
    for hs in HousingSearch.query.filter(HousingSearch.owner == current_user):
        predicates.append(hs.query_predicate())

    listings = Listing.query.filter(or_(*predicates)).order_by(Listing.created.desc())

    return render_template('search/home.html', listings=listings)

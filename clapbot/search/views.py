import datetime as dt
import io

from flask import Blueprint, render_template, current_app
from flask import redirect, url_for, flash

from flask_login import current_user, login_required

from sqlalchemy import or_

from ..core import db
from ..cl.model import Listing, scrape
from .model import HousingSearch
from .model.location import BoundingBox, export_bboxes, iter_bboxes
from .forms import HousingSearchCreate, HousingSearchEditForm, BoundingBoxEditor, SelectBoundingBoxForm

bp = Blueprint('search', __name__)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():

    form = HousingSearchCreate()
    if form.validate_on_submit():
        if len(current_user.housing_searches) >= current_app.config['CRAIGSLIST_MAX_USER_SEARCHES']:
            flash(f"{current_user.username} has exceeded maximum searches")
            return redirect(url_for('user.profile', username=current_user.username))

        hs = HousingSearch(
            name=form.name.data,
            description=form.description.data,
            target_date=dt.datetime.combine(form.target_date.data, dt.time(0, 0, 0)),
            created_at=dt.datetime.now(),
            site=form.site.data,
            owner=current_user)

        expires = hs.target_date + dt.timedelta(days=30)
        if (expires - dt.datetime.now()) > dt.timedelta(days=90):
            expires = dt.datetime.now() + dt.timedelta(days=90)

        hs.expiration_date = expires
        db.session.add(hs)
        db.session.commit()
        current_app.logger.info("Created a new search setting.")
        return redirect(url_for('user.profile', username=current_user.username))

    return render_template('search/new.html', form=form)


@bp.route('/<identifier>/delete', methods=['DELETE', 'POST'])
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


@bp.route('/<int:identifier>')
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


@bp.route('/bbox/create', methods=['GET', 'POST'])
@login_required
def create_bbox():
    """Create bboxes via CSV entry"""

    form = BoundingBoxEditor()

    if form.validate_on_submit():

        stream = io.StringIO(form.bboxes.data)
        for bbox in iter_bboxes(stream):
            bbox.user = current_user
            db.session.add(bbox)

        db.session.commit()
        return redirect(url_for('user.profile', username=current_user.username))

    else:
        if not form.bboxes.data:
            bboxes = BoundingBox.query.filter(BoundingBox.user == current_user)
            bboxes_csv = io.StringIO()
            export_bboxes(bboxes_csv, bboxes)

            form.bboxes.data = bboxes_csv.getvalue()

    return render_template('search/bboxes.html', form=form)


@bp.route('/<identifier>/bbox/', methods=['GET', 'POST'])
@login_required
def set_bbox(identifier):
    """A view for setting the bboxes which belong to a search"""

    hs = HousingSearch.query.get_or_404(identifier)

    bboxes = BoundingBox.query.filter(BoundingBox.user == current_user).all()

    form = SelectBoundingBoxForm.make(bboxes)

    if form.validate_on_submit():

        selected = []
        for field in form.fields:
            if field.type == "BooleanField" and field.data:
                selected.append(BoundingBox.query.get_or_404(field.render_kw['data-bbox']))

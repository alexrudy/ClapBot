import datetime as dt

from flask import Blueprint, render_template, current_app
from flask import redirect, url_for, flash

from flask_login import current_user, login_required

from ..core import db
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
            return redirect(url_for('.create'))

        hs = HousingSearch(
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
        return redirect(url_for('.view'))

    return render_template('search/new.html', form=form)


@bp.route('/')
def view():
    return render_template('search/view.html', searches=current_user.housing_searches)


@bp.route('/<identifier>')
def edit(identifier):
    return "coming soon"
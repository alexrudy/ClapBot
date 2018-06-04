from flask_wtf import FlaskForm
from wtforms import SubmitField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Required
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from ..cl.model import CraigslistSite


def enabled_sites():
    return CraigslistSite.query.filter_by(enabled=True)


class HousingSearchForm(FlaskForm):
    description = TextAreaField()

    target_date = DateField(validators=[DataRequired()])

    site = QuerySelectField(
        'CraigslistSite', validators=[Required()], query_factory=enabled_sites)
    submit = SubmitField('Create')
from flask_wtf import FlaskForm
from wtforms import SubmitField, DateField, TextAreaField, IntegerField, HiddenField, FormField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from ..cl.model import CraigslistSite, CraigslistCategory, CraigslistArea


def enabled_sites():
    return CraigslistSite.query.filter_by(enabled=True)


def enabled_categories():
    return CraigslistCategory.query


def enabled_areas():
    return CraigslistArea.query


class HousingSearchCreate(FlaskForm):
    description = TextAreaField()
    target_date = DateField(validators=[DataRequired()])
    site = QuerySelectField('CraigslistSite', validators=[DataRequired()], query_factory=enabled_sites)

    submit = SubmitField('Create')


class HousingSearchEditForm(FlaskForm):
    """Form for inline editing of housing searches"""

    description = TextAreaField()
    target_date = DateField(validators=[DataRequired()])

    price_min = IntegerField('Max Price ($)', validators=[NumberRange(min=0), DataRequired()])
    price_max = IntegerField('Min Price ($)', validators=[NumberRange(min=0), DataRequired()])

    area = QuerySelectField(
        'Area', query_factory=enabled_areas, allow_blank=True, blank_text='ALL - (Search all areas)')
    category = QuerySelectField('Category', validators=[DataRequired()], query_factory=enabled_categories)

    submit = SubmitField('Save')

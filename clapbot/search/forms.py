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

    def __init__(self, search, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search = search
        self.search_id.data = search.id
        self.description.data = search.description
        self.target_date.data = search.target_date
        self.price_min.data = search.price_min
        self.price_max.data = search.price_max
        self.area.data = search.area
        self.area.query = CraigslistArea.query.filter_by(site=search.site)
        self.category.data = search.category

    search_id = HiddenField()
    description = TextAreaField()
    target_date = DateField(validators=[DataRequired()])

    price_min = IntegerField(validators=[NumberRange(min=0), DataRequired()])
    price_max = IntegerField(validators=[NumberRange(min=0), DataRequired()])

    area = QuerySelectField('CraigslistArea', query_factory=enabled_sites)
    category = QuerySelectField('CraigslistCategory', validators=[DataRequired()], query_factory=enabled_categories)

    submit = SubmitField('Save')

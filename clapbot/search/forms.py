from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, TextAreaField, IntegerField, HiddenField, FormField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from ..cl.model import site


def enabled_sites():
    return site.Site.query.filter_by(enabled=True)


def enabled_categories():
    return site.Category.query


def enabled_areas():
    return site.Area.query


class HousingSearchCreate(FlaskForm):
    name = StringField(validators=[DataRequired()])
    description = TextAreaField()
    target_date = DateField(validators=[DataRequired()])
    site = QuerySelectField(site.Site, validators=[DataRequired()], query_factory=enabled_sites)

    submit = SubmitField('Create')


class HousingSearchEditForm(FlaskForm):
    """Form for inline editing of housing searches"""

    name = StringField(validators=[DataRequired()])

    description = TextAreaField()
    target_date = DateField(validators=[DataRequired()])

    price_min = IntegerField('Max Price ($)', validators=[NumberRange(min=0), DataRequired()])
    price_max = IntegerField('Min Price ($)', validators=[NumberRange(min=0), DataRequired()])

    area = QuerySelectField(
        'Area', query_factory=enabled_areas, allow_blank=True, blank_text='ALL - (Search all areas)')
    category = QuerySelectField('Category', validators=[DataRequired()], query_factory=enabled_categories)

    submit = SubmitField('Save')


class BoundingBoxEditor(FlaskForm):
    """Form for bulk-editing a bounding box."""

    bboxes = TextAreaField(validators=[DataRequired()])

    submit = SubmitField('Save')


def _as_attr(name):
    return name.replace(" ", "_").replace("-", "_")


class SelectBoundingBoxForm(FlaskForm):

    submit = SubmitField('Save')

    @classmethod
    def make(cls, bboxes):
        """Make a series of checkboxes for bboxes."""

        class Form(cls):
            pass

        for bbox in bboxes:
            setattr(Form, _as_attr(bbox.name), BooleanField(label=bbox.name, render_kw={'data-bbox': bbox.id}))

        return Form

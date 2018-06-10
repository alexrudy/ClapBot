import logging
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from .model import User, UserStatus

logger = logging.getLogger(__name__)


class LoginForm(FlaskForm):
    """Used to handle login actions to the website."""
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """Used to handle new user registration requests"""
    username = StringField('User Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).one_or_none()
        if user is not None:
            logger.info("User %s tried to register, username already exist", username.data)
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).one_or_none()
        if user is None:
            logger.info("User %s tried to register but does not exist", email.data)
            raise ValidationError('Please use a different email address.')

        if user is not None and user.status != UserStatus.registered:
            logger.info("User %s tried to register already exists", email.data)
            raise ValidationError('Please use a different email address.')
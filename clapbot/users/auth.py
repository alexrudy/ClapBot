from werkzeug.urls import url_parse

from flask import Blueprint, redirect, url_for, render_template, flash, request

from flask_login import current_user, login_user, logout_user

from ..core import db

from .model import User, UserStatus
from .forms import LoginForm, RegistrationForm

bp = Blueprint('auth', __name__, template_folder='templates')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('.login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('core.home')

        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('core.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).one_or_none()
        if user is None or user.status != UserStatus.registered:
            flash('Invalid email')
            return redirect(url_for('.login'))

        user.set_password(form.password.data)
        user.status = UserStatus.active
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered ClapBot user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)
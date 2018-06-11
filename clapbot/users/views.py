from flask import Blueprint, redirect, url_for, render_template, flash, request, abort

from flask_login import current_user, login_required

from .model import User

bp = Blueprint('user', __name__, template_folder='templates')


@bp.route('/profile/<username>')
@login_required
def profile(username):
    if current_user.username != username:
        abort(404)
    user = User.query.filter_by(username=username).first_or_404()

    return render_template('users/profile.html', user=user)

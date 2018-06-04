import enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from ..core import db, login

roles_users = db.Table(
    'roles_users', db.Column('user_id', db.Integer(),
                             db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('roles.id')))


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __eq__(self, other):
        return (self.name == other
                or self.name == getattr(other, 'name', None))

    def __ne__(self, other):
        return (self.name != other
                and self.name != getattr(other, 'name', None))


class UserStatus(enum.Enum):
    registered = 1
    active = 2
    deactivated = 3


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password = db.Column(db.String(120))

    status = db.Column(
        db.Enum(UserStatus), default=UserStatus.registered, nullable=False)
    created = db.Column(db.DateTime)

    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return 'User(email={})'.format(self.email)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def is_active(self):
        return self.status == UserStatus.active

    @property
    def censored_email(self):
        return "***@" + self.email.split("@", 1)[1]


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

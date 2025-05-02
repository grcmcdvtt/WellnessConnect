from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from datetime import datetime
from sqlalchemy import Enum


# ──────────────── Company Model ──────────────── #

class Company(db.Model):
    __tablename__ = 'companies'

    company_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), unique=True)

    admin = db.relationship(
        'User',
        foreign_keys=[admin_user_id],
        backref='managed_company',
        uselist=False
    )

    users = db.relationship(
        'User',
        backref='company',
        lazy=True,
        foreign_keys='User.company_id'
    )

    vouchers = db.relationship('Voucher', backref='company', lazy=True)


# ──────────────── User Model ──────────────── #

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(20))
    profile_picture = db.Column(db.String(255))
    spendable_points = db.Column(db.Integer, default=0)
    cumulative_points = db.Column(db.Integer, default=0)
    streak_count = db.Column(db.Integer, default=0)

    role = db.Column(Enum("Customer", "SystemAdmin", "CompanyAdmin", name="user_roles"),
                     nullable=False, default="Customer")

    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id', ondelete='SET NULL'))

    reminders = db.relationship("Reminder", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

# ──────────────── Activity Log ──────────────── #

class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)

    activity_type = db.Column(
        Enum('water', 'steps', 'exercise', 'sleep', name='activity_type_enum'),
        nullable=False
    )
    value = db.Column(db.Numeric, nullable=False)

    unit = db.Column(
        Enum('oz', 'steps', 'miles', 'hours', 'minutes', 'km', name='unit_enum'),
        nullable=True
    )

    exercise_type = db.Column(
        Enum('yoga', 'run', 'cycling', 'strength', "other", name='exercise_type_enum'),
        nullable=True
    )

    proof = db.Column(db.Boolean, default=False)
    proof_valid = db.Column(db.Boolean, nullable=True)
    proof_url = db.Column(db.String(255), nullable=True)

    logged_at = db.Column(db.DateTime, default=datetime.utcnow)


# ──────────────── Vouchers ──────────────── #

class Voucher(db.Model):
    __tablename__ = 'vouchers'

    voucher_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cost_in_points = db.Column(db.Integer, nullable=False)
    available_quantity = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'))

class UserVoucher(db.Model):
    __tablename__ = 'user_vouchers'

    user_voucher_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.voucher_id'), nullable=False)
    redeemed = db.Column(db.Boolean, default=False)
    redeemed_at = db.Column(db.DateTime)
    acquired_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='user_vouchers')
    voucher = db.relationship('Voucher', backref='user_vouchers')

# ──────────────── Reminders ──────────────── #

class Reminder(db.Model):
    __tablename__ = 'reminders'
    reminder_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    reminder_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(149), nullable=False)
    send_sms = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)
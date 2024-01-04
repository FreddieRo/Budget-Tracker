from . import db
from flask_login import UserMixin


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    description = db.Column(db.String(50))
    amount = db.Column(db.Numeric(19, 4))
    category = db.Column(db.String(50))
    date = db.Column(db.String(20))
    archived = db.Column(db.Integer, default=0)
    type = db.Column(db.String(50))
    fixed_id = db.Column(db.Integer, db.ForeignKey("fixed.id"), default=None)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150))
    budget = db.Column(db.Integer, default=0)
    budget_start = db.Column(db.String(20))
    budget_end = db.Column(db.String(20))
    budget_time = db.Column(db.String(1000))
    expenses = db.relationship("Expense")
    archivedinfo = db.relationship("ArchivedInfo")
    fixed = db.relationship("Fixed")


class Fixed(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    fixed_amount = db.Column(db.Numeric(2))
    timeframe = db.Column(db.String(30))
    renewal_date = db.Column(db.String(20))
    last_payment = db.Column(db.String(20))
    status = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    expenses = db.relationship("Expense")


class ArchivedInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget = db.Column(db.Integer, default=0)
    budget_start = db.Column(db.String(20))
    budget_end = db.Column(db.String(20))
    budget_time = db.Column(db.String(1000))
    total = db.Column(db.Numeric(2), default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
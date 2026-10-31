
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class Incident(db.Model):
    # Unique ID for each incident
    id = db.Column(db.Integer, primary_key=True)

    # Short incident title and detailed description
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Incident classification and workflow status
    priority = db.Column(db.String(20), default="Medium", nullable=False)
    status = db.Column(db.String(20), default="Open", nullable=False)

    # Assignment details
    assigned_to = db.Column(db.String(100), nullable=True)

    # Automatically record when the incident is created
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )



from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="Reporter", nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

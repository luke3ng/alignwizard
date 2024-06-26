from main import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    # Relationship to link User to their Patients
    patients = db.relationship('Patient', backref='user', lazy=True)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship to link Patient to their Images
    images = db.relationship('Image', backref='patient', lazy=True)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_front = db.Column(db.String(20))
    image_back = db.Column(db.String(20))
    image_left = db.Column(db.String(20))
    image_right = db.Column(db.String(20))
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

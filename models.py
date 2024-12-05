from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

from datetime import datetime, timezone

db = SQLAlchemy(app)


# Users Table
class User(db.Model):
    __tablename__ = "users"
    registration_number = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(
        db.Enum("student", "tutor", "admin", name="user_roles"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    student = db.relationship("Student", back_populates="user", uselist=False)
    tutor = db.relationship("Tutor", back_populates="user", uselist=False)


# Students Table
class Student(db.Model):
    __tablename__ = "students"
    registration_number = db.Column(
        db.String(20), db.ForeignKey("users.registration_number"), primary_key=True
    )
    current_year = db.Column(db.Integer, nullable=False)
    id_card = db.Column(db.Text, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="student")
    requests = db.relationship("Request", back_populates="student")
    reviews = db.relationship("Review", back_populates="student")


# Tutors Table
class Tutor(db.Model):
    __tablename__ = "tutors"
    registration_number = db.Column(
        db.String(20), db.ForeignKey("users.registration_number"), primary_key=True
    )
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Enum("A", "S", name="cgpa_levels"), nullable=False)
    grade_history = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    rating = db.Column(db.Float, default=0.0)

    # Relationships
    user = db.relationship("User", back_populates="tutor")
    slots = db.relationship("Slot", back_populates="tutor")


# Slots Table
class Slot(db.Model):
    __tablename__ = "slots"
    id = db.Column(db.Integer, primary_key=True)
    tutor_registration_number = db.Column(
        db.String(20), db.ForeignKey("tutors.registration_number"), nullable=False
    )
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    gmeet_link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    slot_status = db.Column(
        db.Enum("upcoming", "ongoing", "completed", name="slot_status"),
        default="upcoming",
    )

    # Relationships
    tutor = db.relationship("Tutor", back_populates="slots")
    requests = db.relationship("Request", back_populates="slot")
    reviews = db.relationship("Review", back_populates="slot")


# Requests Table
class Request(db.Model):
    __tablename__ = "requests"
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey("slots.id"), nullable=False)
    student_registration_number = db.Column(
        db.String(20), db.ForeignKey("students.registration_number"), nullable=False
    )
    status = db.Column(
        db.Enum("pending", "accepted", "rejected", name="request_status"),
        default="pending",
    )
    request_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    slot = db.relationship("Slot", back_populates="requests")
    student = db.relationship("Student", back_populates="requests")


# Reviews Table
class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey("slots.id"), nullable=False)
    student_registration_number = db.Column(
        db.String(20), db.ForeignKey("students.registration_number"), nullable=False
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    slot = db.relationship("Slot", back_populates="reviews")
    student = db.relationship("Student", back_populates="reviews")


# Admin Notices Table
class Notice(db.Model):
    __tablename__ = "notices"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))


with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        password_hash = generate_password_hash("admin123")
        admin = User(
            registration_number="admin123",
            name="admin",
            email="admin@gmail.com",
            password_hash=password_hash,
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()

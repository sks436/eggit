import os
from flask import (
    request,
    url_for,
    redirect,
    flash,
    render_template,
    send_from_directory,
)
from app import app
from models import *
from controllers_login import *
from controllers import *
from utils import auth_required
from sqlalchemy import func


# Create a new notice
@app.route("/admin/create_notice", methods=["POST"])
@auth_required
def create_notice():
    if request.method == "POST":
        notice_title = request.form.get("title")
        notice_content = request.form.get("notice")

        if not notice_title or not notice_content:
            flash("Title and content are required!")
            return redirect(url_for("dashboard"))

        new_notice = Notice(title=notice_title, content=notice_content)

        db.session.add(new_notice)
        db.session.commit()

        flash("Notice created successfully!")

        return redirect(url_for("dashboard"))


# Deletes a tutor and their associated data
@app.route("/admin/delete_tutor/<string:registration_number>", methods=["POST"])
@auth_required
def delete_tutor(registration_number):
    user = User.query.filter_by(registration_number=registration_number).first()
    tutor = Tutor.query.filter_by(registration_number=registration_number).first()

    if not tutor:
        flash("Tutor not found")
        return redirect(url_for("dashboard"))

    # Delete grade history file if exists
    if tutor.grade_history:
        try:
            os.remove(tutor.grade_history)
            flash("Grade history file deleted successfully")
        except Exception as e:
            flash(f"Failed to delete grade history file: {e}")

    db.session.delete(tutor)
    db.session.delete(user)
    db.session.commit()

    flash("Tutor deleted successfully")

    return redirect(url_for("show_tutors"))


# Deletes a student and their associated data
@app.route("/admin/delete_student/<string:registration_number>", methods=["POST"])
@auth_required
def delete_student(registration_number):
    user = User.query.filter_by(registration_number=registration_number).first()
    student = Student.query.filter_by(registration_number=registration_number).first()

    # Delete associated requests
    requests = Request.query.filter_by(
        student_registration_number=registration_number
    ).all()

    for req in requests:
        db.session.delete(req)

    # Delete ID card file if exists
    if student.id_card:
        try:
            os.remove(student.id_card)
            flash("ID Card file deleted successfully")
        except Exception as e:
            flash(f"Failed to delete ID card file: {e}")

    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()

    flash("Student deleted successfully")

    return redirect(url_for("show_students"))


# Deletes a slot and its associated requests and rebiews
@app.route("/admin/delete_slot/<int:slot_id>", methods=["POST"])
@auth_required
def delete_slot(slot_id):
    slot = Slot.query.filter_by(id=slot_id).first()
    tutor = Tutor.query.filter_by(
        registration_number=slot.tutor_registration_number
    ).first()

    if slot:
        # Delete associated requests
        for req in slot.requests:
            db.session.delete(req)

        # Delete associated reviews
        reviews = Review.query.filter_by(slot_id=slot.id).all()

        for review in reviews:
            db.session.delete(review)
        db.session.delete(slot)
        db.session.commit()

        # Average rating of the tutor
        average_rating = (
            db.session.query(func.avg(Review.rating))
            .join(Slot, Review.slot_id == Slot.id)
            .filter(Slot.tutor_registration_number == tutor.registration_number)
            .scalar()
        )

        # Update tutor's rating (rounded to 2 decimals)
        if average_rating is not None:
            tutor.rating = round(average_rating, 2)

            db.session.commit()

        flash("Slot deleted successfully")

    else:
        flash("Slot not found")

    return redirect(url_for("show_slots"))


# Deletes a notice by its ID
@app.route("/admin/delete_notice/<int:notice_id>", methods=["POST"])
@auth_required
def delete_notice(notice_id):
    notice = Notice.query.get(notice_id)

    if notice:
        db.session.delete(notice)
        db.session.commit()
        flash("Notice deleted successfully!")

    else:
        flash("Notice not found")

    return redirect(url_for("dashboard"))


# Displays all tutors
@app.route("/admin/show_tutors", methods=["GET", "POST"])
@auth_required
def show_tutors():
    tutors = db.session.query(Tutor).join(User).all()

    return render_template("show_tutors.html", tutors=tutors)


# Displays all students
@app.route("/admin/show_students", methods=["GET", "POST"])
@auth_required
def show_students():
    students = db.session.query(Student).join(User).all()

    return render_template("show_students.html", students=students)


# Displays upcoming, ongoing, and completed slots
@app.route("/admin/show_slots", methods=["GET", "POST"])
@auth_required
def show_slots():
    upcoming_slots = (
        Slot.query.join(Tutor).join(User).filter(Slot.slot_status == "upcoming").all()
    )

    ongoing_slots = (
        Slot.query.join(Tutor).join(User).filter(Slot.slot_status == "ongoing").all()
    )

    completed_slots = (
        Slot.query.join(Tutor).join(User).filter(Slot.slot_status == "completed").all()
    )

    # Fetch completed slots with average ratings
    slots_completed = (
        db.session.query(Slot, func.avg(Review.rating).label("average_rating"))
        .outerjoin(Review, Review.slot_id == Slot.id)
        .filter(Slot.slot_status == "completed")
        .group_by(Slot.id)
        .all()
    )

    return render_template(
        "show_slots.html",
        upcoming_slots=upcoming_slots,
        ongoing_slots=ongoing_slots,
        completed_slots=completed_slots,
        slots_completed=slots_completed,
    )


# Displays reviews for a specific slot
@app.route("/admin/show_reviews/<string:slot_id>", methods=["POST"])
@auth_required
def show_reviews(slot_id):
    reviews = (
        Review.query.filter(Review.slot_id == slot_id)
        .join(User, User.registration_number == Review.student_registration_number)
        .add_columns(User.name)
        .all()
    )

    return render_template("show_reviews.html", reviews=reviews)


# Serves uploaded files
@app.route("/admin/uploads/<string:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["IMAGES"], filename)

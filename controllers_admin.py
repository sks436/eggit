import os
from flask import (
    request,
    url_for,
    redirect,
    flash,
    render_template,
    send_from_directory,
    session,
)
from app import app
from models import *
from controllers_login import *
from controllers import *
from utils import auth_required
from sqlalchemy import func


@app.route("/admin/create_notice", methods=["POST"])
@auth_required
def create_notice():
    """Creates a new notice."""
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


@app.route("/admin/delete_tutor/<string:registration_number>", methods=["POST"])
@auth_required
def delete_tutor(registration_number):
    """Deletes a tutor and their associated data."""
    user = User.query.filter_by(registration_number=registration_number).first()
    tutor = Tutor.query.filter_by(registration_number=registration_number).first()

    if not tutor:
        flash("Tutor not found")
        return redirect(url_for("dashboard"))

    # Delete associated slots and requests
    slots = Slot.query.filter_by(tutor_registration_number=registration_number).all()
    for slot in slots:
        requests = Request.query.filter_by(slot_id=slot.id).all()
        for req in requests:
            db.session.delete(req)
        db.session.delete(slot)

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


@app.route("/admin/delete_student/<string:registration_number>", methods=["POST"])
@auth_required
def delete_student(registration_number):
    """Deletes a student and their associated data."""
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


@app.route("/admin/delete_slot/<int:slot_id>", methods=["POST"])
@auth_required
def delete_slot(slot_id):
    """Deletes a slot and its associated requests."""
    slot = Slot.query.filter_by(id=slot_id).first()

    if slot:
        # Delete associated requests
        for req in slot.requests:
            db.session.delete(req)

        db.session.delete(slot)
        db.session.commit()

        flash("Slot deleted successfully")
    else:
        flash("Slot not found")

    return redirect(url_for("show_slots"))


@app.route("/admin/delete_notice/<int:notice_id>", methods=["POST"])
@auth_required
def delete_notice(notice_id):
    """Deletes a notice by its ID."""
    notice = Notice.query.get(notice_id)

    if notice:
        db.session.delete(notice)
        db.session.commit()
        flash("Notice deleted successfully!")
    else:
        flash("Notice not found")

    return redirect(url_for("dashboard"))


@app.route("/admin/show_tutors", methods=["GET", "POST"])
@auth_required
def show_tutors():
    """Displays all tutors."""
    tutors = db.session.query(Tutor).join(User).all()
    return render_template("show_tutors.html", tutors=tutors)


@app.route("/admin/show_students", methods=["GET", "POST"])
@auth_required
def show_students():
    """Displays all students."""
    students = db.session.query(Student).join(User).all()
    return render_template("show_students.html", students=students)


@app.route("/admin/show_slots", methods=["GET", "POST"])
@auth_required
def show_slots():
    """Displays upcoming, ongoing, and completed slots."""
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


@app.route("/admin/uploads/<string:filename>")
def uploaded_file(filename):
    """Serves uploaded files."""
    return send_from_directory(app.config["IMAGES"], filename)

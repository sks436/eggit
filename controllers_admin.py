import os
from flask import url_for, redirect, flash
from app import app
from models import *
from controllers_login import *
from utils import auth_required


# Delete Tutor
@app.route("/admin/delete_tutor/<string:registration_number>", methods=["POST"])
@auth_required
def delete_tutor(registration_number):
    user = User.query.filter_by(registration_number=registration_number).first()
    tutor = Tutor.query.filter_by(registration_number=registration_number).first()

    if not tutor:
        flash("Tutor not found")
        return redirect(url_for("dashboard"))

    slots = Slot.query.filter_by(tutor_registration_number=registration_number).all()
    for slot in slots:
        requests = Request.query.filter_by(slot_id=slot.id).all()
        for request in requests:
            db.session.delete(request)
        db.session.delete(slot)

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


# Delete Student
@app.route("/admin/delete_student/<string:registration_number>", methods=["POST"])
@auth_required
def delete_student(registration_number):
    user = User.query.filter_by(registration_number=registration_number).first()
    student = Student.query.filter_by(registration_number=registration_number).first()
    requests = Request.query.filter_by(
        student_registration_number=registration_number
    ).all()

    for request in requests:
        db.session.delete(request)

    if student.id_card:
        try:
            os.remove(student.id_card)
            flash("ID Card file deleted successfully")
        except Exception as e:
            flash(f"Failed to delete id card file: {e}")

    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    flash("Student deleted successfully")
    return redirect(url_for("show_students"))


# Show Tutors
@app.route("/admin/show_tutors", methods=["POST"])
@auth_required
def show_tutors():
    tutors = db.session.query(Tutor).join(User).all()

    return render_template("show_tutors.html", tutors=tutors)


# Show Student
@app.route("/admin/show_students", methods=["POST"])
@auth_required
def show_students():
    students = db.session.query(Student).join(User).all()

    return render_template("show_students.html", students=students)

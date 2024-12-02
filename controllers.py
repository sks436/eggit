from flask import render_template, request, url_for, redirect, flash, session, Response
from app import app
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps
from controllers_login import *
import io
import csv


def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for("home"))

    return inner


# Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
@auth_required
def dashboard():
    user = User.query.get(session["user_id"])

    if user.role == "tutor":
        tutor = Tutor.query.filter_by(
            registration_number=user.registration_number
        ).first()
        slots = Slot.query.filter_by(
            tutor_registration_number=tutor.registration_number
        ).all()
        requests = (
            Request.query.join(Slot)
            .filter(Slot.tutor_registration_number == tutor.registration_number)
            .all()
        )
        if "delete" in request.args:
            slot_id=request.args.get("slot_id")
            slot=Slot.query.filter_by(id=slot_id).first()
            requests=Request.query.filter_by(slot_id=slot_id).all()
            for r in requests:
                db.session.delete(r)
            db.session.delete(slot)
            db.session.commit()
            return redirect(url_for("dashboard"))
        return render_template(
            "tutor.html", user=user, tutor=tutor, slots=slots, requests=requests
        )

    elif user.role == "student":
        student = Student.query.filter_by(
            registration_number=user.registration_number
        ).first()
        slots = (
            db.session.query(
                Slot.id,
                Slot.subject,
                Slot.date,
                Slot.time,
                Tutor.registration_number,
                User.name.label("tutor_name"),
            )
            .join(Tutor, Slot.tutor_registration_number == Tutor.registration_number)
            .join(User, User.registration_number == Tutor.registration_number)
            .all()
        )
        upcoming = (
            Request.query.join(Slot)
            .filter(
                Request.student_registration_number == user.registration_number,
                Request.status == "accepted",
            )
            .all()
        )
        pending = (
            Request.query.join(Slot)
            .filter(
                Request.student_registration_number == user.registration_number,
                Request.status == "pending",
            )
            .all()
        )
        return render_template(
            "student.html",
            user=user,
            student=student,
            slots=slots,
            upcoming=upcoming,
            pending=pending,
        )

    elif user.role == "admin":
        tutors = Tutor.query.all() 
        students = Student.query.all() 
        return render_template("admin.html", user=user, tutors=tutors, students=students)

# Create slot
@app.route("/create_slot", methods=["GET", "POST"])
@auth_required
def create_slot():
    if request.method == "GET":
        return render_template("create_slot.html")
    else:
        # Retrieve data from the form
        subject = request.form.get("subject")
        date = request.form.get("date")
        time = request.form.get("time")
        link = request.form.get("gmeet_link")

        # Validate the form data
        if not subject or not date or not time:
            flash("All fields are required to create a slot.", "danger")
            return redirect(url_for("create_slot"))

        # Ensure the logged-in user is a tutor
        user_id = session.get("user_id")
        tutor = Tutor.query.filter_by(registration_number=user_id).first()
        if not tutor:
            flash("Only tutors can create slots.", "danger")
            return redirect(url_for("dashboard"))

        # Parse date and time to proper formats
        try:
            slot_date = datetime.strptime(date, "%Y-%m-%d").date()
            slot_time = datetime.strptime(time, "%H:%M").time()
        except ValueError:
            flash(
                "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time.",
                "danger",
            )
            return redirect(url_for("create_slot"))

        # Check for duplicate slots
        existing_slot = Slot.query.filter_by(
            tutor_registration_number=tutor.registration_number,
            date=slot_date,
            time=slot_time,
        ).first()

        if existing_slot:
            flash("A slot already exists for the specified date and time.", "danger")
            return redirect(url_for("create_slot"))

        # Create the slot and save it to the database
        new_slot = Slot(
            tutor_registration_number=tutor.registration_number,
            subject=subject,
            date=slot_date,
            time=slot_time,
            gmeet_link=link,
        )

        db.session.add(new_slot)
        db.session.commit()

        flash("Slot created successfully!", "success")
        return redirect(url_for("dashboard"))


# Request for slot
@app.route("/request_slot/<int:slot_id>", methods=["GET", "POST"])
@auth_required
def request_slot(slot_id):
    user = User.query.get(session["user_id"])
    if user.role != "student":
        return "Unauthorized", 403

    # Check if the slot exists
    slot = Slot.query.get(slot_id)
    if not slot:
        return "Slot not found", 404

    # Check if the student already requested this slot
    existing_request = Request.query.filter_by(
        slot_id=slot_id, student_registration_number=user.registration_number
    ).first()
    if existing_request:
        flash("You have already requested this slot.", "danger")
        return redirect(url_for("dashboard"))
    else:
        # Create a new request
        new_request = Request(
            slot_id=slot_id,
            student_registration_number=user.registration_number,
            status="pending",
        )
        db.session.add(new_request)
        db.session.commit()

        return redirect("/dashboard")


# Update request
@app.route("/update_request/<int:request_id>", methods=["POST"])
@auth_required
def update_request(request_id):
    if request.method == "POST":
        user = User.query.get(session["user_id"])
        if user.role != "tutor":
            return "Unauthorized", 403

        # Find the request
        requests = Request.query.get(request_id)
        if not requests:
            return "Request not found", 404

        # Ensure the tutor owns the slot
        slot = Slot.query.get(requests.slot_id)
        if slot.tutor_registration_number != user.registration_number:
            return "Unauthorized", 403

        # Update request status
        action = request.form.get("action")
        if action == "accept":
            requests.status = "accepted"
        elif action == "reject":
            requests.status = "rejected"
        else:
            return "Invalid action", 400

        db.session.commit()
        return redirect(url_for("slot_request", slot_id=slot.id))
    else:
        return "This endpoint only handles POST requests", 405


@app.route("/slot_request/<int:slot_id>", methods=["GET", "POST"])
@auth_required
def slot_request(slot_id):
    user = User.query.get(session["user_id"])
    tutor = Tutor.query.filter_by(registration_number=user.registration_number).first()
    requests = (
        Request.query.join(Slot)
        .filter(
            Slot.tutor_registration_number == tutor.registration_number,
            Request.slot_id == slot_id,
        )
        .all()
    )
    emails = (
        Request.query.join(Slot)
        .filter(
            Slot.tutor_registration_number == tutor.registration_number,
            Request.slot_id == slot_id,
            Request.status == "accepted",
        )
        .all()
    )
    email_list = []
    for mails in emails:
        email_list.append(mails.student.user.email)

    if "download" in request.args:
        # Generate CSV file
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows([[email] for email in email_list]) 
        output.seek(0)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=emails.csv"}
        )
    return render_template("slot_request.html", user=user, requests=requests)

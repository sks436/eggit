from flask import render_template, request, url_for, redirect, flash, session, Response
from app import app
from models import *
from controllers_login import *
from controllers_admin import *
import io
import csv
from utils import auth_required
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from sqlalchemy import func


# Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
@auth_required
def dashboard():
    user = User.query.get(session["user_id"])
    # Get the 3 most recent notices
    notices = Notice.query.order_by(Notice.created_at.desc()).limit(3).all()

    # Tutor
    if user.role == "tutor":
        tutor = Tutor.query.filter_by(
            registration_number=user.registration_number
        ).first()

        slots = Slot.query.filter_by(
            tutor_registration_number=tutor.registration_number, slot_status="upcoming"
        ).all()

        # Fetch completed slots with average ratings
        slots_completed = (
            db.session.query(Slot, func.avg(Review.rating).label("average_rating"))
            .outerjoin(Review, Review.slot_id == Slot.id)
            .filter(
                Slot.tutor_registration_number == tutor.registration_number,
                Slot.slot_status == "completed",
            )
            .group_by(Slot.id)
            .all()
        )

        ongoing = Slot.query.filter_by(
            tutor_registration_number=tutor.registration_number, slot_status="ongoing"
        ).all()

        requests = (
            Request.query.join(Slot)
            .filter(Slot.tutor_registration_number == tutor.registration_number)
            .all()
        )

        if "delete" in request.args:
            slot_id = request.args.get("slot_id")
            slot = Slot.query.filter_by(id=slot_id).first()
            requests = Request.query.filter_by(slot_id=slot_id).all()
            for r in requests:
                db.session.delete(r)
            db.session.delete(slot)
            db.session.commit()
            return redirect(url_for("dashboard"))
        
        return render_template(
            "tutor.html",
            user=user,
            tutor=tutor,
            slots=slots,
            requests=requests,
            slots_completed=slots_completed,
            ongoing=ongoing,
            notices=notices,
        )

    # Student
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
                Slot.tutor_registration_number,
                Slot.slot_status,
                Tutor.registration_number,
                User.name.label("tutor_name"),
            )
            .join(Tutor, Slot.tutor_registration_number == Tutor.registration_number)
            .join(User, User.registration_number == Tutor.registration_number)
            .filter(Slot.slot_status == "upcoming")
            .all()
        )

        upcoming = (
            Request.query.join(Slot)
            .join(User, User.registration_number == Slot.tutor_registration_number)
            .filter(
                Request.student_registration_number == user.registration_number,
                Request.status == "accepted",
                Slot.slot_status == "upcoming",
            )
            .with_entities(Request, Slot, User.name)  # Select specific columns/entities
            .all()
        )
        ongoing = (
            Request.query.join(Slot)
            .join(User, User.registration_number == Slot.tutor_registration_number)
            .filter(
                Request.student_registration_number == user.registration_number,
                Request.status == "accepted",
                Slot.slot_status == "ongoing",
            )
            .with_entities(Request, Slot, User.name)
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
            ongoing=ongoing,
            notices=notices,
        )

    # Admin
    elif user.role == "admin":
        tutors = Tutor.query.all()
        students = Student.query.all()
        notices_all = Notice.query.order_by(Notice.created_at.desc()).all()

        return render_template(
            "admin.html",
            user=user,
            tutors=tutors,
            students=students,
            notices=notices_all,
        )

    else:
        return redirect(url_for("dashboard"))


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
        duration = request.form.get("duration")
        link = request.form.get("gmeet_link")

        # Validate the form data
        if not subject or not date or not time or not duration:
            flash("All fields are required to create a slot.", "danger")
            return redirect(url_for("create_slot"))

        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError("Duration must be positive.")
        except ValueError:
            flash(
                "Invalid duration. Please enter a valid number greater than zero.",
                "danger",
            )
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

        # Calculate the start and end times for the new slot
        slot_start = datetime.combine(slot_date, slot_time)
        slot_end = slot_start + timedelta(minutes=duration)

        # Fetch existing slots to check for overlap
        overlapping_slot = Slot.query.filter(
            Slot.tutor_registration_number == tutor.registration_number,
            Slot.date == slot_date,
        ).all()  # Fetch all existing slots for the tutor on that date

        # Check for overlap with existing slots in Python
        for existing_slot in overlapping_slot:
            existing_slot_start = datetime.combine(
                existing_slot.date, existing_slot.time
            )
            existing_slot_end = existing_slot_start + timedelta(
                minutes=existing_slot.duration
            )

            # If there's an overlap, return error
            if (existing_slot_start < slot_end) and (slot_start < existing_slot_end):
                flash(
                    "A slot clash exists for the specified time and duration.", "danger"
                )
                return redirect(url_for("create_slot"))

        # Create the slot and save it to the database
        new_slot = Slot(
            tutor_registration_number=tutor.registration_number,
            subject=subject,
            date=slot_date,
            time=slot_time,
            duration=duration,
            gmeet_link=link,
        )

        db.session.add(new_slot)
        db.session.commit()

        flash("Slot created successfully!", "success")
        return redirect(url_for("dashboard"))


# Request slot
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

    # Check if the student already has an accepted slot at the same time
    conflicting_slot = (
        db.session.query(Slot)
        .join(Request)
        .filter(
            Request.student_registration_number == user.registration_number,
            Request.status == "accepted",
            Slot.slot_status == "upcoming",  # Only check for upcoming slots
            Slot.date == slot.date,  # Same date
            Slot.time == slot.time,  # Same time
        )
        .first()
    )

    if conflicting_slot:
        flash("You already have an accepted class at this time.", "danger")
        return redirect(url_for("dashboard"))

    # Create a new request if no conflicts
    new_request = Request(
        slot_id=slot_id,
        student_registration_number=user.registration_number,
        status="pending",
    )
    db.session.add(new_request)
    db.session.commit()

    flash("Request for the slot has been made.", "success")
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
    slot=Slot.query.filter_by(id=slot_id).first()
    if slot.slot_status=="upcoming" and slot.tutor_registration_number==user.registration_number:
        tutor = Tutor.query.filter_by(registration_number=user.registration_number).first()
        requests = (
            Request.query.join(Slot)
            .filter(
                Slot.tutor_registration_number == tutor.registration_number,
                Request.slot_id == slot_id,
            )
            .all()
        )
        requests_count = (
            db.session.query(func.count(Request.id))
            .filter(Request.slot_id == slot_id, Request.status == "accepted")
            .scalar()
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
                headers={"Content-Disposition": "attachment; filename=emails.csv"},
            )
        return render_template(
            "slot_request.html", user=user, requests=requests, requests_count=requests_count
        )
    else:
        flash("Not allowed")
        return redirect(url_for('dashboard'))


@app.route("/tutor_profile/<string:tutor_registration_number>", methods=["POST"])
@auth_required
def tutor_profile(tutor_registration_number):
    tutor = (
        db.session.query(Tutor)
        .join(User)
        .filter(Tutor.registration_number == tutor_registration_number)
        .first()
    )

    return render_template("tutor_profile.html", tutor=tutor)


@app.route("/student/completed_slots", methods=["GET", "POST"])
@auth_required
def completed_slots():
    user = User.query.get(session["user_id"])
    slots_completed = (
        db.session.query(Request, Slot, User.name, Review)
        .join(Slot, Request.slot_id == Slot.id)
        .join(User, Slot.tutor_registration_number == User.registration_number)
        .outerjoin(
            Review,
            (Review.slot_id == Slot.id)
            & (Review.student_registration_number == user.registration_number),
        )
        .filter(
            Request.student_registration_number == user.registration_number,
            Slot.slot_status == "completed",
        )
        .all()
    )

    return render_template("completed_slots.html", slots_completed=slots_completed)


# Submit review on completed slot
@app.route("/submit_review/<int:slot_id>", methods=["POST"])
def submit_review(slot_id):
    # Ensure the student is logged in and has attended the class
    student = Student.query.filter_by(registration_number=session["user_id"]).first()
    if not student:
        return "Unauthorized", 403

    # Ensure the student is linked to the slot
    slot = Slot.query.get(slot_id)
    # if not slot or slot.student_registration_number != student.registration_number:
    #     return "You are not authorized to review this slot", 403

    # Ensure the class status is 'completed'
    if slot.slot_status != "completed":
        return "This class is not completed yet", 400

    # Get the rating and comment from the form
    rating = request.form.get("rating")
    comment = request.form.get("comment")

    # Validate rating (should be an integer between 1 and 5)
    if not rating or not (1 <= int(rating) <= 5):
        return "Invalid rating. Please provide a rating between 1 and 5.", 400

    # Check if a review already exists for this student and slot
    existing_review = Review.query.filter_by(
        student_registration_number=student.registration_number, slot_id=slot_id
    ).first()
    if existing_review:
        return "You have already submitted a review for this class", 400

    # Create a new review entry
    review = Review(
        slot_id=slot_id,
        student_registration_number=student.registration_number,
        rating=int(rating),
        comment=comment,
    )

    # Save the review to the database
    db.session.add(review)
    db.session.commit()

    tutor = Tutor.query.filter_by(
        registration_number=slot.tutor_registration_number
    ).first()

    if tutor:
        # Calculate the average rating from all reviews for this tutor
        average_rating = (
            db.session.query(func.avg(Review.rating))
            .join(Slot, Review.slot_id == Slot.id)
            .filter(Slot.tutor_registration_number == tutor.registration_number)
            .scalar()
        )

        if average_rating is not None:
            tutor.rating = round(
                average_rating, 2
            )  # Update tutor's rating (rounded to 2 decimals)
            db.session.commit()

    return redirect(url_for("completed_slots"))  # Redirect to slot details page


# Update slot status automatically
def update_slot_status():
    with app.app_context():
        now = datetime.now()
        slots = Slot.query.all()

        for slot in slots:
            slot_start_datetime = datetime.combine(slot.date, slot.time)
            slot_end_datetime = slot_start_datetime + timedelta(minutes=slot.duration)

            if slot_start_datetime <= now < slot_end_datetime:
                slot.slot_status = "ongoing"
            elif now >= slot_end_datetime:
                slot.slot_status = "completed"
            else:
                slot.slot_status = "upcoming"

        db.session.commit()


# Scheduler to schedle the slot status automatically
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_slot_status, trigger="interval", seconds=30)
scheduler.start()

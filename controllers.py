from flask import render_template,request,url_for,redirect,flash, session
from app import app
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps
from controllers_login import *

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for("home"))
    return inner


#Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
@auth_required
def dashboard():
    user = User.query.get(session['user_id'])

    if user.role=='tutor':
        tutor=Tutor.query.filter_by(registration_number=user.registration_number).first()
        slots=Slot.query.filter_by(tutor_registration_number=tutor.registration_number).all()
        requests = Request.query.join(Slot).filter(Slot.tutor_registration_number == tutor.registration_number).all()
        return render_template("tutor.html",user=user,tutor=tutor,slots=slots,requests=requests)
    
    elif user.role=='student':
        student=Student.query.filter_by(registration_number=user.registration_number).first()
        slots = (db.session.query(
        Slot.id,
        Slot.subject,
        Slot.date,
        Slot.time,
        Tutor.registration_number,
        User.name.label('tutor_name')).join(Tutor, Slot.tutor_registration_number == Tutor.registration_number) \
        .join(User, User.registration_number == Tutor.registration_number)
        .all()
        )
        upcoming = Request.query.join(Slot).filter(
            Request.student_registration_number == user.registration_number,
            Request.status == 'accepted'
        ).all()
        return render_template("student.html",user=user,student=student,slots=slots,upcoming=upcoming)
    
    elif user.role=='admin':
        return render_template("admin.html")
    

    
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
        link= request.form.get("gmeet_link")

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
            flash("Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time.", "danger")
            return redirect(url_for("create_slot"))

        # Check for duplicate slots
        existing_slot = Slot.query.filter_by(
            tutor_registration_number=tutor.registration_number,
            date=slot_date,
            time=slot_time
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
            gmeet_link=link
        )

        db.session.add(new_slot)
        db.session.commit()

        flash("Slot created successfully!", "success")
        return redirect(url_for("dashboard"))

#Request for slot
@app.route("/request_slot/<int:slot_id>", methods=["GET","POST"])
@auth_required
def request_slot(slot_id):
    user = User.query.get(session['user_id'])
    if user.role != 'student':
        return "Unauthorized", 403
    
    # Check if the slot exists
    slot = Slot.query.get(slot_id)
    if not slot:
        return "Slot not found", 404
    
    # Check if the student already requested this slot
    existing_request = Request.query.filter_by(
        slot_id=slot_id,
        student_registration_number=user.registration_number
    ).first()
    if existing_request:
        flash("You have already requested this slot.", "danger")
        redirect(url_for("dashboard"))
    
    # Create a new request
    new_request = Request(
        slot_id=slot_id,
        student_registration_number=user.registration_number,
        status='pending'
    )
    db.session.add(new_request)
    db.session.commit()
    
    return redirect("/dashboard")

#Update request
@app.route("/update_request/<int:request_id>", methods=["POST"])
@auth_required
def update_request(request_id):
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        if user.role != 'tutor':
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
        if action == 'accept':
            requests.status = 'accepted'
        elif action == 'reject':
            requests.status = 'rejected'
        else:
            return "Invalid action", 400
    
        db.session.commit()
        return redirect("/dashboard")
    else:
        return "This endpoint only handles POST requests", 405


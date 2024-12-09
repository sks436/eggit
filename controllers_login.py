from flask import render_template, request, url_for, redirect, flash, session
from app import app
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from utils import auth_required
from controllers_admin import *
import smtplib
import secrets
import datetime
from email.mime.text import MIMEText


# Login page
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")

        if not login_id or not password:
            flash("Please fill in all fields")
            return redirect(url_for("home"))

        user = User.query.filter_by(registration_number=login_id).first()

        if not user:
            flash("User does not exist")
            return redirect(url_for("home"))

        if not check_password_hash(user.password_hash, password):
            flash("Incorrect password")
            return redirect(url_for("home"))

        session["user_id"] = user.registration_number

        flash("Login successfully")
        return redirect(url_for("dashboard"))

    else:
        if "user_id" in session:
            session.pop("user_id")

        return render_template("login.html")


# Tutor registration
@app.route("/register_tutor", methods=["GET", "POST"])
def register_tutor():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        registration_number = request.form.get("registration_number")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        subject = request.form.get("subject")
        grade = request.form.get("grade")
        description = request.form.get("description")
        file = request.files.get("grade_history")

        if not name or not password or not confirm_password:
            flash("Please fill all fields")
            return redirect(url_for("register_tutor"))

        elif password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("register_tutor"))

        user = User.query.filter_by(
            registration_number=registration_number, role="tutor"
        ).first()

        if user:
            flash("User already exists")
            return redirect(url_for("register_tutor"))

        if not os.path.exists(app.config["IMAGES"]):
            os.makedirs(app.config["IMAGES"])

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["IMAGES"], filename)
        file.save(file_path)

        new_tutor = Tutor(
            registration_number=registration_number + "_tutor",
            subject=subject,
            grade=grade,
            description=description,
            grade_history=file_path,
        )

        db.session.add(new_tutor)
        db.session.commit()

        password_hash = generate_password_hash(password)
        new_user = User(
            registration_number=registration_number + "_tutor",
            name=name,
            email=email,
            password_hash=password_hash,
            role="tutor",
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully")
        flash(f"Your Login Id is {registration_number}_tutor")
        return redirect(url_for("home"))

    else:
        if "user_id" in session:
            session.pop("user_id")

        return render_template("register_tutor.html")


# Student registration
@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        registration_number = request.form.get("registration_number")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        current_year = request.form.get("current_year")
        file = request.files.get("id_card")

        if not name or not password or not confirm_password:
            flash("Please fill all fields")
            return redirect(url_for("register_student"))

        elif password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("register_student"))

        user = User.query.filter_by(
            registration_number=registration_number, role="student"
        ).first()

        if user:
            flash("User already exists")
            return redirect(url_for("register_student"))

        if not os.path.exists(app.config["IMAGES"]):
            os.makedirs(app.config["IMAGES"])

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["IMAGES"], filename)
        file.save(file_path)

        new_student = Student(
            registration_number=registration_number,
            current_year=current_year,
            id_card=file_path,
        )

        db.session.add(new_student)
        db.session.commit()

        password_hash = generate_password_hash(password)
        new_user = User(
            registration_number=registration_number,
            name=name,
            email=email,
            password_hash=password_hash,
            role="student",
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully")
        flash(f"Your Login Id is {registration_number}")

        return redirect(url_for("home"))

    else:
        if "user_id" in session:
            session.pop("user_id")

        return render_template("register_student.html")


# Logout
@app.route("/logout")
@auth_required
def logout():
    session.pop("user_id")
    flash("Logged out successfully")

    return redirect(url_for("home"))


# Profile
@app.route("/profile", methods=["GET", "POST"])
@auth_required
def profile():
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        name = request.form.get("name")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")

        if not current_password or not new_password or not confirm_password:
            flash("Please fill out all the required fields")
            return redirect(url_for("profile"))

        if not check_password_hash(user.password_hash, current_password):
            flash("Incorrect password")
            return redirect(url_for("profile"))

        if new_password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("profile"))

        new_password_hash = generate_password_hash(new_password)
        user.name = name
        user.password_hash = new_password_hash
        user.email = email

        db.session.commit()

        flash("Profile updated successfully")

        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


# Send OTP function
def send_otp(email, otp):
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = os.getenv("SMTP_PORT")

    message = MIMEText(f"Your OTP for password reset is: {otp}\n Valid for 10 minutes.")
    message["Subject"] = "Eggit: Password Reset OTP"
    message["From"] = EMAIL_ADDRESS
    message["To"] = email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(message)


# Forgot password
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if "user_id" in session:
        session.pop("user_id")

    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            otp = secrets.token_hex(3)
            user.otp = otp
            user.otp_expiration = datetime.datetime.now() + datetime.timedelta(
                minutes=10
            )

            db.session.commit()

            send_otp(email, otp)

            flash("An OTP has been sent to your email.")

            return redirect(url_for("verify_otp", email=email))
        else:
            flash("Email not found.")

    return render_template("forgot_password.html")


# Verify OPT
@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    global otp_global

    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()

    if request.method == "POST":
        otp = request.form.get("otp")

        if user and user.otp == otp and datetime.datetime.now() < user.otp_expiration:
            otp_global = otp

            return redirect(url_for("reset_password", email=email, otp=otp))

        else:
            flash("Invalid or expired OTP.")

    return render_template("verify_otp.html", email=email)


# Reset password
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    email = request.args.get("email")
    otp = request.args.get("otp")

    if otp_global != otp:
        flash("Not allowed")
        return redirect(url_for("home"))

    user = User.query.filter_by(email=email).first()

    if request.method == "POST":
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("reset_password"))

        user.password_hash = generate_password_hash(new_password)

        user.otp = None
        user.otp_expiration = None

        db.session.commit()
        flash("Your password has been reset successfully.")

        return redirect(url_for("home"))

    return render_template("reset_password.html", email=email)


# Search students, tutors and slots accordingly for associated users
@app.route("/search", methods=["GET"])
@auth_required
def search():
    category = request.args.get("category")
    query = request.args.get("query")
    user = User.query.get(session["user_id"])

    students = []
    tutors = []
    slots = []

    if category == "students" and query:
        students = (
            db.session.query(Student)
            .join(User)
            .filter(
                User.name.ilike(f"%{query}%")
                | Student.registration_number.ilike(f"%{query}%")
            )
            .all()
        )

    elif category == "tutors" and query:
        tutors = (
            db.session.query(Tutor)
            .join(User)
            .filter(
                User.name.ilike(f"%{query}%")
                | Tutor.subject.ilike(f"%{query}%")
                | Tutor.registration_number.ilike(f"%{query}%")
            )
            .all()
        )

    elif category == "subjects" and query:
        slots = (
            db.session.query(Slot)
            .join(Tutor)
            .filter(Slot.subject.ilike(f"%{query}%"))
            .all()
        )

    if user.role == "tutor":
        slots_tutor = (
            db.session.query(Slot)
            .filter(
                Slot.tutor_registration_number == user.registration_number,
                Slot.slot_status == "upcoming",
                Slot.subject.ilike(f"%{query}%"),
            )
            .all()
        )

    elif user.role == "student":
        slots_students = (
            db.session.query(Slot)
            .join(Tutor)
            .filter(Slot.slot_status == "upcoming", Slot.subject.ilike(f"%{query}%"))
            .all()
        )

    if user.role == "student":
        return render_template(
            "search.html",
            category=category,
            query=query,
            tutors=tutors,
            slots=slots_students,
            user=user,
        )

    elif user.role == "tutor":
        return render_template(
            "search.html",
            category=category,
            query=query,
            slots=slots_tutor,
            user=user,
        )

    else:
        return render_template(
            "search.html",
            category=category,
            query=query,
            students=students,
            tutors=tutors,
            slots=slots,
            user=user,
        )

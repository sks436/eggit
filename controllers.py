from flask import render_template, request, url_for, redirect, flash, session
from app import app
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os


# Login page
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        reg_number = request.form.get("login")
        password = request.form.get("password")

        if not reg_number or not password:
            flash("Please fill in all fields")
            return redirect(url_for("home"))

        user = User.query.filter_by(registration_number=reg_number).first()
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
        return render_template("index.html")


# Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user.role == "tutor":
            tutor = Tutor.query.filter_by(
                registration_number=user.registration_number
            ).first()
            return render_template("tutor.html", user=user, tutor=tutor)
        elif user.role == "student":
            student = Student.query.filter_by(
                registration_number=user.registration_number
            ).first()
            return render_template("student.html", user=user, student=student)
        if user.role == "admin":
            return render_template("admin.html")
    else:
        flash("Please login to continue")
        return redirect(url_for("home"))


# Tutor registration
@app.route("/register_tutor", methods=["GET", "POST"])
def register_tutor():
    if request.method == "POST":
        name = request.form.get("full_name")
        email = request.form.get("email")
        reg_number = request.form.get("reg_number")
        password = request.form.get("password")
        cnf_password = request.form.get("cnf_password")
        subject = request.form.get("subject")
        cgpa = request.form.get("grade")
        description = request.form.get("description")
        file = request.files.get("grade_history")

        if not name or not password or not cnf_password:
            flash("Please fill all fields")
            return redirect(url_for("register_tutor"))

        elif password != cnf_password:
            flash("Passwords do not match")
            return redirect(url_for("register_tutor"))

        user = User.query.filter_by(
            registration_number=reg_number, role="tutor"
        ).first()
        if user:
            flash("User already exists")
            return redirect(url_for("register_tutor"))

        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        new_tutor = Tutor(
            registration_number=reg_number + "_tutor",
            subject=subject,
            cgpa=cgpa,
            description=description,
            grade_history=file_path,
        )
        db.session.add(new_tutor)
        db.session.commit()

        password_hash = generate_password_hash(password)
        new_user = User(
            registration_number=reg_number + "_tutor",
            name=name,
            email=email,
            password_hash=password_hash,
            role="tutor",
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registered successfully")
        flash("Your Login Id is Registration Number_tutor")
        return redirect(url_for("home"))

    else:
        return render_template("register_tutor.html")


# Student registration
@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        f_name = request.form.get("first_name")
        l_name = request.form.get("last_name")
        name = f_name + " " + l_name
        email = request.form.get("email")
        reg_number = request.form.get("reg_number")
        password = request.form.get("password")
        cnf_password = request.form.get("cnf_password")
        year = request.form.get("year")
        file = request.files.get("idCard")

        if not name or not password or not cnf_password:
            flash("Please fill all fields")
            return redirect(url_for("register_student"))

        elif password != cnf_password:
            flash("Passwords do not match")
            return redirect(url_for("register_student"))

        user = User.query.filter_by(
            registration_number=reg_number, role="student"
        ).first()
        if user:
            flash("User already exists")
            return redirect(url_for("register_student"))

        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        new_student = Student(
            registration_number=reg_number, year_of_study=year, id_card_image=file_path
        )
        db.session.add(new_student)
        db.session.commit()

        password_hash = generate_password_hash(password)
        new_user = User(
            registration_number=reg_number,
            name=name,
            email=email,
            password_hash=password_hash,
            role="student",
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registered successfully")
        flash("Your Login Id is Registration Number")
        return redirect(url_for("home"))

    else:
        return render_template("register_student.html")

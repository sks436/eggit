from flask import render_template, request, url_for, redirect, flash
from app import app
from models import *
from werkzeug.security import generate_password_hash, check_password_hash


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

        return render_template("dashboard.html", x="Shivang")

    else:
        return render_template("index.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    return render_template("dashboard.html")


@app.route("/register_tutor", methods=["GET", "POST"])
def register_tutor():
    if request.method == "POST":
        name = request.form.get("full_name")
        email = request.form.get("email")
        reg_number = request.form.get("reg_number")
        password = request.form.get("password")
        cnf_password = request.form.get("cnf_password")
        subject = request.form.get("subject")

        if not name or not password or not cnf_password:
            flash("Please fill all fields")
            return redirect(url_for("register_tutor"))

        elif password != cnf_password:
            flash("Passwords do not match")
            return redirect(url_for("register_tutor"))

        user = User.query.filter_by(registration_number=reg_number).first()
        if user:
            flash("User already exists")
            return redirect(url_for("register_tutor"))

        password_hash = generate_password_hash(password)

        new_user = User(
            registration_number=reg_number,
            name=name,
            email=email,
            password_hash=password_hash,
            role="tutor",
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("home"))

    else:
        return render_template("register_tutor.html")


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

        if not name or not password or not cnf_password:
            flash("Please fill all fields")
            return redirect(url_for("register_student"))

        elif password != cnf_password:
            flash("Passwords do not match")
            return redirect(url_for("register_student"))

        user = User.query.filter_by(registration_number=reg_number).first()
        if user:
            flash("User already exists")
            return redirect(url_for("register_student"))

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
        return redirect(url_for("home"))

    else:
        return render_template("register_student.html")

from flask import render_template,request,url_for,redirect,flash, session
from app import app
from models import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps
from controllers import *

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for("home"))
    return inner

#Login page
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        login_id=request.form.get("login_id")
        password=request.form.get("password")

        if not login_id or not password:
            flash("Please fill in all fields")
            return redirect(url_for("home"))
        
        user=User.query.filter_by(registration_number=login_id).first()
        if not user:
            flash("User does not exist")
            return redirect(url_for("home"))
        
        if not check_password_hash(user.password_hash, password):
            flash("Incorrect password")
            return redirect(url_for("home"))
        
        session['user_id']=user.registration_number
        flash("Login successfully")
        return redirect(url_for("dashboard"))
        
    else:
        return render_template("login.html")
    
#Tutor registration
@app.route("/register_tutor", methods=["GET", "POST"])
def register_tutor():
    if request.method == "POST":
        name=request.form.get("name")
        email=request.form.get("email")
        registration_number=request.form.get("registration_number")
        password=request.form.get("password")
        confirm_password=request.form.get("confirm_password")
        subject=request.form.get("subject")
        grade=request.form.get("grade")
        description=request.form.get("description")
        file = request.files.get('grade_history')

        if not name or not password or not confirm_password:
            flash("Please fill all fields")
            return redirect(url_for('register_tutor'))
        
        elif password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for('register_tutor'))
        
        user=User.query.filter_by(registration_number=registration_number, role="tutor").first()
        if user:
            flash("User already exists")
            return redirect(url_for('register_tutor'))
        
        if not os.path.exists(app.config['IMAGES']):
            os.makedirs(app.config['IMAGES'])

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['IMAGES'], filename)
        file.save(file_path)
        
        new_tutor=Tutor(registration_number=registration_number+"_tutor", subject=subject, grade=grade, description=description, grade_history=file_path)
        db.session.add(new_tutor)
        db.session.commit()

        password_hash=generate_password_hash(password)
        new_user=User(registration_number=registration_number+"_tutor", name=name, email=email, password_hash=password_hash, role="tutor")
        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully")
        flash("Your Login Id is Registration Number_tutor")
        return redirect(url_for("home"))
        
    else:
        return render_template("register_tutor.html")

#Student registration
@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        name=request.form.get("name")
        email=request.form.get("email")
        registration_number=request.form.get("registration_number")
        password=request.form.get("password")
        confirm_password=request.form.get("confirm_password")
        current_year=request.form.get("current_year")
        file=request.files.get("id_card")

        if not name or not password or not confirm_password:
            flash("Please fill all fields")
            return redirect(url_for('register_student'))
        
        elif password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for('register_student'))
        
        user=User.query.filter_by(registration_number=registration_number, role="student").first()
        if user:
            flash("User already exists")
            return redirect(url_for('register_student'))
        
        if not os.path.exists(app.config['IMAGES']):
            os.makedirs(app.config['IMAGES'])

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['IMAGES'], filename)
        file.save(file_path)

        new_student=Student(registration_number=registration_number, current_year=current_year, id_card=file_path)
        db.session.add(new_student)
        db.session.commit()

        password_hash=generate_password_hash(password)
        new_user=User(registration_number=registration_number, name=name, email=email, password_hash=password_hash, role="student")
        db.session.add(new_user)
        db.session.commit()
        
        flash("Registered successfully")
        flash("Your Login Id is Registration Number")
        return redirect(url_for("home"))
    
    else:
        return  render_template("register_student.html")
    

#Logout
@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    flash("Logged out successfully")
    return redirect(url_for("home"))
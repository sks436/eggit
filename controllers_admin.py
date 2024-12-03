from flask import render_template, request, url_for, redirect, flash, session, Response
from app import app
from models import *
from functools import wraps
from controllers_login import *
from controllers import *

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "user_id" in session:
            return func(*args, **kwargs)
        else:
            flash("Please login to continue")
            return redirect(url_for("home"))

    return inner

@app.route("/admin/delete_tutor/<string:registration_number>", methods=["POST"])
@auth_required
def delete_tutor(registration_number):
    user = User.query.filter_by(registration_number=registration_number).first()
    tutor = Tutor.query.filter_by(registration_number=registration_number).first()
    slots = Slot.query.filter_by(
        tutor_registration_number=registration_number
    ).all()

    for slot in slots:
        requests = Request.query.filter_by(slot_id=slot.id).all()
        for request in requests:
            db.session.delete(request)
        db.session.delete(slot)

    db.session.delete(tutor)
    db.session.delete(user)
    db.session.commit()
    flash("Tutor deleted successfully")
    return redirect(url_for('dashboard'))
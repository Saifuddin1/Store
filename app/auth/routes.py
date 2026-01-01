from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from app.models import User
from app import db,bcrypt
from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, is_active=True).first()

        if user and user.check_password(password):
            login_user(user)

            user.last_login = datetime.utcnow()
            db.session.commit()

            # ✅ ROLE-BASED REDIRECT
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            else:
                return redirect(url_for("main.dashboard"))

        flash("Invalid email or password", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            email=email,
            password=hashed_password,
            is_active=True
        )

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created successfully!", "success")

        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")

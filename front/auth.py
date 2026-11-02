from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from extensions import db, limiter
from model.models import User
from helper import load_users, save_users, check_password, upload_image
from . import user_bp


@user_bp.route("/auth", methods=["GET"])
def auth():
    mode = request.args.get("mode", "login")
    return render_template("front/auth.html", mode=mode)


@user_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.args.get("next") or request.form.get("next")

        # 1. Try Database User
        user = User.query.filter_by(email=email).first()
        if user and check_password(password, user.password):
            session.clear()
            session.permanent = bool(request.form.get("remember"))
            session["user_id"] = user.id
            session["user_email"] = user.email
            session["username"] = user.fullname or user.email.split("@")[0]
            session["user_role"] = user.role
            session["role"] = user.role
            session["user_image"] = user.profile_image or user.image

            # -------------------------------------------------------------
            # ROLE-BASED REDIRECTION:
            # Admins go to Admin Dashboard, Regular Customers go to User Page
            # -------------------------------------------------------------
            if user.role == "Admin":
                session["admin_logged_in"] = True
                session["admin_name"] = user.fullname or user.email.split("@")[0]
                flash(f"Welcome to Admin Dashboard, {user.fullname or 'Administrator'}!", "success")
                # If explicit next_url points to a checkout or admin page, respect it; otherwise go to admin dashboard
                if next_url and not next_url.startswith("/account"):
                    return redirect(next_url)
                return redirect(url_for("admin.admin_dashboard"))

            # Regular Customer
            flash("Welcome back!", "success")
            return redirect(next_url or url_for("user.account"))

        # 2. Fallback to JSON Users
        json_user = load_users().get(email)
        if json_user and check_password(password, json_user.get("password", "")):
            session.clear()
            session.permanent = bool(request.form.get("remember"))
            session["user_id"] = json_user.get("id", 1)
            session["user_email"] = email
            user_name = json_user.get("name", email.split("@")[0])
            user_role = json_user.get("role", "Customer")
            session["username"] = user_name
            session["user_role"] = user_role
            session["role"] = user_role
            session["user_image"] = json_user.get("image") or "https://arthurmillerfoundation.org/wp-content/uploads/2018/06/default-placeholder.png"

            if user_role == "Admin":
                session["admin_logged_in"] = True
                session["admin_name"] = user_name
                flash(f"Welcome to Admin Dashboard, {user_name}!", "success")
                if next_url and not next_url.startswith("/account"):
                    return redirect(next_url)
                return redirect(url_for("admin.admin_dashboard"))

            flash("Welcome back!", "success")
            return redirect(next_url or url_for("user.account"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("user.login", next=next_url, mode="login"))

    return render_template("front/auth.html", mode="login")


@user_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        next_url = request.args.get("next") or request.form.get("next")

        if User.query.filter_by(email=email).first() or email in load_users():
            flash("This email is already registered. Please log in.", "warning")
            return redirect(url_for("user.login", next=next_url, mode="login"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("user.register", next=next_url, mode="register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return redirect(url_for("user.register", next=next_url, mode="register"))

        # Handle Profile Image upload (formfile only)
        image_file = request.files.get("image")
        uploaded_image_url = None
        if image_file and image_file.filename:
            uploaded_image_url = upload_image(image_file)

        profile_img_url = uploaded_image_url or "https://arthurmillerfoundation.org/wp-content/uploads/2018/06/default-placeholder.png"
        hashed_pwd = generate_password_hash(password)

        # Save to Database Model
        new_db_user = User(
            fullname=name,
            email=email,
            password=hashed_pwd,
            image=profile_img_url,
            role="Customer",
            status="Active"
        )
        db.session.add(new_db_user)
        db.session.commit()

        # Also backup to JSON users
        users = load_users()
        users[email] = {
            "name": name,
            "email": email,
            "password": hashed_pwd,
            "image": profile_img_url,
        }
        save_users(users)

        session.clear()
        session["user_id"] = new_db_user.id
        session["user_email"] = email
        session["username"] = name
        session["user_role"] = "Customer"
        session["role"] = "Customer"
        session["user_image"] = profile_img_url
        flash("Account created successfully! Welcome to SV7@168.", "success")
        return redirect(next_url or url_for("user.account"))

    return render_template("front/auth.html", mode="register")


@user_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("user.login"))


@user_bp.route("/reset-password", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def reset_password():
    if request.method == "POST":
        flash("Password reset link sent.", "info")
        return redirect(url_for("user.login"))
    return render_template("front/forgot-password.html")
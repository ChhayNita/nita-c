from flask import render_template, request, flash, redirect, url_for, session
from extensions import db
from model.models import User
from helper import login_required, upload_image, load_users, save_users
from . import user_bp


@user_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user = None
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
    if not user and session.get("user_email"):
        user = User.query.filter_by(email=session.get("user_email")).first()

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        image_file = request.files.get("image")

        if user:
            if fullname:
                user.fullname = fullname
                session["username"] = fullname

            if image_file and image_file.filename:
                new_image_url = upload_image(image_file)
                if new_image_url:
                    user.image = new_image_url
                    session["user_image"] = new_image_url

            db.session.commit()

            # Also update JSON backup if exists
            users = load_users()
            if user.email in users:
                if fullname:
                    users[user.email]["name"] = fullname
                if user.image:
                    users[user.email]["image"] = user.image
                save_users(users)

            flash("Profile updated successfully!", "success")
            return redirect(url_for("user.account"))

    return render_template("front/account.html", user=user)
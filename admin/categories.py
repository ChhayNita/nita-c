from flask import render_template, request, redirect, url_for, flash
from extensions import db
from model import Category, Product
from helper import upload_image
from decorators import admin_required
from . import admin_bp


DEFAULT_CATEGORY_IMAGE = "https://arthurmillerfoundation.org/wp-content/uploads/2018/06/default-placeholder.png"


@admin_bp.route("/categories")
@admin_required
def admin_categories():
    categories = Category.query.order_by(Category.id.desc()).all()
    return render_template(
        "admin/category/index.html",
        active_page="category",
        categories=categories
    )


@admin_bp.route("/categories/add", methods=["GET", "POST"])
@admin_required
def admin_category_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for("admin.admin_category_add"))

        # Check duplicate category name
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash(f'Category "{name}" already exists.', "warning")
            return redirect(url_for("admin.admin_category_add"))

        # Check uploaded image file
        image_path = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename:
                image_path = upload_image(file)

        # Use default placeholder if no image was uploaded
        if not image_path:
            image_path = DEFAULT_CATEGORY_IMAGE

        category = Category(
            name=name,
            image=image_path,
            description=description
        )
        db.session.add(category)
        db.session.commit()

        flash(f'Category "{name}" created successfully!', "success")
        return redirect(url_for("admin.admin_categories"))

    return render_template("admin/category/add.html", active_page="category")


@admin_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@admin_required
def admin_category_edit(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for("admin.admin_category_edit", category_id=category.id))

        # Check duplicate name with other categories
        existing = Category.query.filter(Category.name == name, Category.id != category.id).first()
        if existing:
            flash(f'Another category with name "{name}" already exists.', "warning")
            return redirect(url_for("admin.admin_category_edit", category_id=category.id))

        # Handle image upload if a new file is chosen
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename:
                new_image = upload_image(file)
                if new_image:
                    category.image = new_image

        category.name = name
        category.description = description

        db.session.commit()
        flash(f'Category "{name}" updated successfully!', "success")
        return redirect(url_for("admin.admin_categories"))

    return render_template("admin/category/edit.html", active_page="category", category=category)


@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
@admin_required
def admin_category_delete(category_id):
    category = Category.query.get_or_404(category_id)

    # Check if category has associated products
    product_count = Product.query.filter_by(CategoryId=category.id).count()
    if product_count > 0:
        flash(f'Cannot delete category "{category.name}" because it still has {product_count} product(s) linked to it.', "danger")
        return redirect(url_for("admin.admin_categories"))

    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{category.name}" has been deleted.', "success")
    return redirect(url_for("admin.admin_categories"))

from flask import render_template, request, redirect, url_for, flash
from extensions import db
from model import Product, Category, ProductImage
from helper import upload_image
from decorators import admin_required
from . import admin_bp


@admin_bp.route("/products")
@admin_required
def admin_products():
    products = Product.query.order_by(Product.id.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template(
        "admin/product/index.html",
        active_page="product",
        products=products,
        categories=categories
    )


DEFAULT_PRODUCT_IMAGE = "https://arthurmillerfoundation.org/wp-content/uploads/2018/06/default-placeholder.png"


@admin_bp.route("/products/add", methods=["GET", "POST"])
@admin_required
def admin_product_add():
    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id")
        cost = request.form.get("cost", "0.00").strip()
        price = request.form.get("price", "0.00").strip()
        stock = request.form.get("stock", "50").strip()
        description = request.form.get("description", "").strip()

        # Validation
        if not name:
            flash("Product name is required.", "danger")
            return redirect(url_for("admin.admin_product_add"))

        if not category_id:
            flash("Please select a category.", "danger")
            return redirect(url_for("admin.admin_product_add"))

        try:
            category_id = int(category_id)
            cost_val = float(cost) if cost else 0.00
            price_val = float(price) if price else 0.00
            stock_val = int(stock) if stock else 0
        except ValueError:
            flash("Invalid numeric value for cost, price, or stock.", "danger")
            return redirect(url_for("admin.admin_product_add"))

        # Process main thumbnail image via formfile
        thumbnail_path = None
        if "thumbnail" in request.files:
            thumb_file = request.files["thumbnail"]
            if thumb_file and thumb_file.filename:
                thumbnail_path = upload_image(thumb_file)

        # Create Product
        product = Product(
            name=name,
            thumbnail=thumbnail_path,
            Cost=cost_val,
            Price=price_val,
            Stock=stock_val,
            CategoryId=category_id,
            description=description
        )
        db.session.add(product)
        db.session.flush()  # Generate product.id for ProductImage

        # =========================================================================
        # Process Multiple Product Images via formfile
        # =========================================================================
        uploaded_images_count = 0
        if "images" in request.files:
            image_files = request.files.getlist("images")
            for img_file in image_files:
                if img_file and img_file.filename:
                    saved_path = upload_image(img_file)
                    if saved_path:
                        product_image = ProductImage(ProductId=product.id, name=saved_path)
                        db.session.add(product_image)
                        uploaded_images_count += 1
                        # If no thumbnail was specified, use first gallery image as thumbnail
                        if not product.thumbnail:
                            product.thumbnail = saved_path

        # If still no thumbnail, fallback to default placeholder
        if not product.thumbnail:
            product.thumbnail = DEFAULT_PRODUCT_IMAGE

        db.session.commit()
        flash(f'Product "{name}" created successfully with {uploaded_images_count} image(s)!', "success")
        return redirect(url_for("admin.admin_products"))

    return render_template("admin/product/add.html", active_page="product", categories=categories)


@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def admin_product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id")
        cost = request.form.get("cost", "0.00").strip()
        price = request.form.get("price", "0.00").strip()
        stock = request.form.get("stock", "0").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Product name is required.", "danger")
            return redirect(url_for("admin.admin_product_edit", product_id=product.id))

        try:
            product.name = name
            product.CategoryId = int(category_id)
            product.Cost = float(cost) if cost else 0.00
            product.Price = float(price) if price else 0.00
            product.Stock = int(stock) if stock else 0
            product.description = description
        except (ValueError, TypeError):
            flash("Invalid input values provided.", "danger")
            return redirect(url_for("admin.admin_product_edit", product_id=product.id))

        # Check new thumbnail upload via formfile
        if "thumbnail" in request.files:
            thumb_file = request.files["thumbnail"]
            if thumb_file and thumb_file.filename:
                new_thumb = upload_image(thumb_file)
                if new_thumb:
                    product.thumbnail = new_thumb

        # Check additional multiple image uploads via formfile
        if "images" in request.files:
            image_files = request.files.getlist("images")
            for img_file in image_files:
                if img_file and img_file.filename:
                    saved_path = upload_image(img_file)
                    if saved_path:
                        product_image = ProductImage(ProductId=product.id, name=saved_path)
                        db.session.add(product_image)

        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', "success")
        return redirect(url_for("admin.admin_products"))

    return render_template("admin/product/edit.html", active_page="product", product=product, categories=categories)


@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def admin_product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{name}" has been deleted.', "success")
    return redirect(url_for("admin.admin_products"))


@admin_bp.route("/products/image/delete/<int:image_id>", methods=["POST"])
@admin_required
def admin_product_image_delete(image_id):
    img = ProductImage.query.get_or_404(image_id)
    product_id = img.ProductId
    db.session.delete(img)
    db.session.commit()
    flash("Product image removed.", "success")
    return redirect(url_for("admin.admin_product_edit", product_id=product_id))
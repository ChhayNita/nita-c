from flask import render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from model import Order, OrderItem
from decorators import admin_required
from . import admin_bp


@admin_bp.route("/orders")
@admin_required
def admin_orders():
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    query = Order.query.order_by(Order.id.desc())
    if search:
        query = query.filter(
            (Order.order_number.ilike(f"%{search}%")) |
            (Order.customer_name.ilike(f"%{search}%")) |
            (Order.customer_phone.ilike(f"%{search}%"))
        )
    if status_filter:
        query = query.filter_by(order_status=status_filter)

    orders = query.all()
    stats = {
        "total": Order.query.count(),
        "pickup": Order.query.filter_by(delivery_type="pickup").count(),
        "delivery": Order.query.filter_by(delivery_type="delivery").count(),
        "khqr": Order.query.filter_by(payment_method="khqr").count(),
    }

    return render_template(
        "admin/order/index.html",
        active_page="orders",
        active_subpage="all",
        page_title="All Orders",
        orders=orders,
        stats=stats,
        search=search,
        status_filter=status_filter
    )


@admin_bp.route("/orders/pickup")
@admin_required
def admin_orders_pickup():
    search = request.args.get("search", "").strip()
    query = Order.query.filter_by(delivery_type="pickup").order_by(Order.id.desc())
    if search:
        query = query.filter(
            (Order.order_number.ilike(f"%{search}%")) |
            (Order.customer_name.ilike(f"%{search}%")) |
            (Order.customer_phone.ilike(f"%{search}%"))
        )
    orders = query.all()
    stats = {
        "total": Order.query.count(),
        "pickup": Order.query.filter_by(delivery_type="pickup").count(),
        "delivery": Order.query.filter_by(delivery_type="delivery").count(),
        "khqr": Order.query.filter_by(payment_method="khqr").count(),
    }

    return render_template(
        "admin/order/pickup.html",
        active_page="orders",
        active_subpage="pickup",
        page_title="Store Pickup Orders",
        orders=orders,
        stats=stats,
        search=search
    )


@admin_bp.route("/orders/khqr")
@admin_required
def admin_orders_khqr():
    search = request.args.get("search", "").strip()
    query = Order.query.filter_by(payment_method="khqr").order_by(Order.id.desc())
    if search:
        query = query.filter(
            (Order.order_number.ilike(f"%{search}%")) |
            (Order.customer_name.ilike(f"%{search}%")) |
            (Order.bakong_md5.ilike(f"%{search}%"))
        )
    orders = query.all()
    stats = {
        "total": Order.query.count(),
        "pickup": Order.query.filter_by(delivery_type="pickup").count(),
        "delivery": Order.query.filter_by(delivery_type="delivery").count(),
        "khqr": Order.query.filter_by(payment_method="khqr").count(),
    }

    return render_template(
        "admin/order/khqr.html",
        active_page="orders",
        active_subpage="khqr",
        page_title="Pay with KHQR (Bakong)",
        orders=orders,
        stats=stats,
        search=search
    )


@admin_bp.route("/orders/delivery")
@admin_required
def admin_orders_delivery():
    search = request.args.get("search", "").strip()
    query = Order.query.filter_by(delivery_type="delivery").order_by(Order.id.desc())
    if search:
        query = query.filter(
            (Order.order_number.ilike(f"%{search}%")) |
            (Order.customer_name.ilike(f"%{search}%")) |
            (Order.shipping_address.ilike(f"%{search}%"))
        )
    orders = query.all()
    stats = {
        "total": Order.query.count(),
        "pickup": Order.query.filter_by(delivery_type="pickup").count(),
        "delivery": Order.query.filter_by(delivery_type="delivery").count(),
        "khqr": Order.query.filter_by(payment_method="khqr").count(),
    }

    return render_template(
        "admin/order/delivery.html",
        active_page="orders",
        active_subpage="delivery",
        page_title="Delivery Orders",
        orders=orders,
        stats=stats,
        search=search
    )


@admin_bp.route("/orders/<int:order_id>")
@admin_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template(
        "admin/order/detail.html",
        active_page="orders",
        active_subpage="all",
        order=order
    )


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_order_update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("order_status", "").strip()
    payment_status = request.form.get("payment_status", "").strip()

    if new_status:
        order.order_status = new_status
    if payment_status:
        order.payment_status = payment_status

    db.session.commit()
    flash(f'Order #{order.order_number} status updated to "{order.order_status}".', "success")
    return redirect(request.referrer or url_for("admin.admin_order_detail", order_id=order.id))


@admin_bp.route("/orders/<int:order_id>/delete", methods=["POST"])
@admin_required
def admin_order_delete(order_id):
    order = Order.query.get_or_404(order_id)
    num = order.order_number
    db.session.delete(order)
    db.session.commit()
    flash(f'Order #{num} deleted.', "success")
    return redirect(url_for("admin.admin_orders"))

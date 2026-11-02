from flask import render_template
from extensions import db
from model import Order, Product, Category, User
from decorators import admin_required
from . import admin_bp


@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    total_orders = Order.query.count()
    pickup_orders = Order.query.filter_by(delivery_type="pickup").count()
    khqr_orders = Order.query.filter_by(payment_method="khqr").count()
    delivery_orders = Order.query.filter_by(delivery_type="delivery").count()
    total_products = Product.query.count()
    total_categories = Category.query.count()
    total_users = User.query.count()

    # Sum total revenue
    paid_orders = Order.query.filter_by(payment_status="Paid").all()
    total_revenue = sum([float(o.total_amount) for o in paid_orders]) if paid_orders else 0.00

    recent_orders = Order.query.order_by(Order.id.desc()).limit(6).all()

    return render_template(
        "admin/dashboard/index.html",
        active_page="dashboard",
        total_revenue=total_revenue,
        total_orders=total_orders,
        pickup_orders=pickup_orders,
        khqr_orders=khqr_orders,
        delivery_orders=delivery_orders,
        total_products=total_products,
        total_categories=total_categories,
        total_users=total_users,
        recent_orders=recent_orders
    )
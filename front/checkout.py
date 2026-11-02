import time
from flask import render_template, request, flash, redirect, url_for, session, jsonify, make_response
from extensions import db, csrf
from model import Order, OrderItem, User
from helper import build_cart_items, send_checkout_notification, redirect_with_cart
from bakong_service import generate_bakong_khqr, check_bakong_payment_status
from . import user_bp


@user_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    # 1. User must register or log in first before payment
    if not session.get("user_id") and not session.get("user_email"):
        flash("Please sign in or create an account before proceeding to payment.", "warning")
        return redirect(url_for("user.login", next=url_for("user.checkout")))

    items, total = build_cart_items()

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("user.cart"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        delivery_type = request.form.get("delivery_type", "delivery").strip().lower()
        address = request.form.get("address", "").strip()
        notes = request.form.get("notes", "").strip()
        payment_method = request.form.get("payment_method", "khqr").strip().lower()

        if not name or not phone:
            flash("Full name and phone number are required.", "danger")
            return redirect(url_for("user.checkout"))

        if delivery_type == "delivery" and not address:
            flash("Shipping address is required for delivery.", "danger")
            return redirect(url_for("user.checkout"))

        if delivery_type == "pickup":
            address = "Store Pickup: SV7 Store Main Branch (Phnom Penh)"

        order_number = f"ORD-{int(time.time())}"

        # -------------------------------------------------------------
        # KHQR PAYMENT FLOW:
        # "in KHQR when status should not pending should not push to db"
        # We DO NOT create an Order in the DB yet while status is pending!
        # -------------------------------------------------------------
        if payment_method == "khqr":
            bill_number = f"INV-{int(time.time())}"
            try:
                khqr_data = generate_bakong_khqr(
                    amount=total,
                    bill_number=bill_number,
                    currency="USD",
                    store_label="SV7 Store"
                )
            except Exception as e:
                flash(f"Error initializing Bakong KHQR: {e}", "danger")
                return redirect(url_for("user.checkout"))

            # Store pending order details temporarily in session
            session["pending_khqr"] = {
                "order_number": order_number,
                "name": name,
                "phone": phone,
                "email": email,
                "delivery_type": delivery_type,
                "address": address,
                "notes": notes,
                "total": total,
                "currency": "USD",
                "bill_number": bill_number,
                "md5": khqr_data["md5"],
                "qr": khqr_data["qr"],
                "qr_image": khqr_data["qr_image"],
                "deeplink": khqr_data["deeplink"],
                "merchant_name": khqr_data["merchant_name"],
                "items": [
                    {
                        "product_id": item["product"]["id"],
                        "product_name": item["product"]["title"],
                        "product_image": item["product"].get("image") or item["product"].get("thumbnail"),
                        "product_price": float(item["product"]["discounted_price"]),
                        "quantity": int(item["quantity"]),
                        "subtotal": float(item["subtotal"])
                    }
                    for item in items
                ]
            }
            return redirect(url_for("user.checkout_khqr"))

        # -------------------------------------------------------------
        # CASH PAYMENT FLOW (Cash on Delivery / Pay on Pickup):
        # Direct save to database with Pending payment status
        # -------------------------------------------------------------
        order = Order(
            order_number=order_number,
            customer_name=name,
            customer_phone=phone,
            customer_email=email,
            delivery_type=delivery_type,
            shipping_address=address,
            notes=notes,
            payment_method="cash",
            payment_status="Pending",
            order_status="Processing",
            total_amount=total,
            currency="USD"
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product"]["id"],
                product_name=item["product"]["title"],
                product_image=item["product"].get("image") or item["product"].get("thumbnail"),
                product_price=float(item["product"]["discounted_price"]),
                quantity=int(item["quantity"]),
                subtotal=float(item["subtotal"])
            )
            db.session.add(order_item)

        db.session.commit()

        # Send Telegram alert
        send_checkout_notification(name, phone, email, address, notes, items, total)
        flash("Order placed successfully!", "success")
        return redirect_with_cart(url_for("user.order_success", order_number=order.order_number), {})

    user = None
    if session.get("user_id"):
        user = User.query.get(session.get("user_id"))
    if not user and session.get("user_email"):
        user = User.query.filter_by(email=session.get("user_email")).first()

    return render_template("front/checkout/checkout.html", items=items, total=total, user=user)


@user_bp.route("/checkout/khqr", methods=["GET"])
def checkout_khqr():
    if not session.get("user_id") and not session.get("user_email"):
        flash("Please sign in or create an account before proceeding to payment.", "warning")
        return redirect(url_for("user.login", next=url_for("user.checkout")))

    pending = session.get("pending_khqr")
    if not pending:
        flash("No active KHQR checkout found.", "warning")
        return redirect(url_for("user.checkout"))

    return render_template(
        "front/checkout/khqr.html",
        pending=pending
    )


@user_bp.route("/api/bakong/check-status", methods=["GET", "POST"])
@csrf.exempt
def api_bakong_check_status():
    pending = session.get("pending_khqr")
    if not pending or not pending.get("md5"):
        return jsonify({"status": "EXPIRED", "message": "Checkout session expired"}), 400

    md5 = pending["md5"]

    # Check status via Bakong API
    status = check_bakong_payment_status(md5)

    # Allow simulation for demo / sandbox testing
    simulate = request.args.get("simulate", "").strip()
    if simulate == "1":
        status = "PAID"

    # CRITICAL: If still UNPAID or PENDING -> DO NOT push to database!
    if status != "PAID":
        return jsonify({
            "status": "PENDING",
            "bakong_status": status,
            "message": "Waiting for customer to scan and pay via Bakong..."
        })

    # ONLY WHEN STATUS IS PAID -> Push to DB!
    # Check if order was already inserted to prevent double submission
    existing = Order.query.filter_by(order_number=pending["order_number"]).first()
    if not existing:
        order = Order(
            order_number=pending["order_number"],
            customer_name=pending["name"],
            customer_phone=pending["phone"],
            customer_email=pending["email"],
            delivery_type=pending["delivery_type"],
            shipping_address=pending["address"],
            notes=pending["notes"],
            payment_method="khqr",
            payment_status="Paid",
            order_status="Processing",
            total_amount=pending["total"],
            currency=pending.get("currency", "USD"),
            bakong_md5=pending["md5"],
            bakong_qr=pending["qr"]
        )
        db.session.add(order)
        db.session.flush()

        for it in pending["items"]:
            order_item = OrderItem(
                order_id=order.id,
                product_id=it["product_id"],
                product_name=it["product_name"],
                product_image=it.get("product_image"),
                product_price=it["product_price"],
                quantity=it["quantity"],
                subtotal=it["subtotal"]
            )
            db.session.add(order_item)

        db.session.commit()

        # Format items for telegram notification
        notif_items = [
            {
                "product": {"title": it["product_name"]},
                "quantity": it["quantity"],
                "subtotal": it["subtotal"]
            }
            for it in pending["items"]
        ]
        send_checkout_notification(
            pending["name"],
            pending["phone"],
            pending["email"],
            pending["address"],
            f"[Paid with Bakong KHQR | MD5: {pending['md5']}] {pending.get('notes', '')}",
            notif_items,
            pending["total"]
        )

    # Pop session now that order is confirmed
    confirmed_order_number = pending["order_number"]
    session.pop("pending_khqr", None)

    # Response instructs frontend to clear cart cookie & redirect to order receipt
    response = make_response(jsonify({
        "status": "PAID",
        "order_number": confirmed_order_number,
        "redirect_url": url_for("user.order_success", order_number=confirmed_order_number)
    }))
    response.delete_cookie("cart")
    return response


@user_bp.route("/order/success/<order_number>")
def order_success(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    response = make_response(render_template("front/checkout/success.html", order=order))
    response.delete_cookie("cart")
    return response
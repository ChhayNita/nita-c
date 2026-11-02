import os
import json
import hashlib
from datetime import datetime
from urllib import request as urllib_request
from urllib.error import URLError

from flask import current_app, redirect, request, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from app.models import User, Product, Category, ProductImage, DEFAULT_PRODUCT_IMAGE
from app.utils.decorators import admin_required, login_required

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
CART_COOKIE = "cart"
CART_MAX_AGE = 60 * 60 * 24 * 30
USERS_FILE = os.path.join(BASE_DIR, "data", "users.json")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_image(file):
    try:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            filename = f"{timestamp}_{filename}"
            upload_dir = current_app.config.get('UPLOAD_FOLDER', UPLOAD_FOLDER) if current_app else UPLOAD_FOLDER
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, filename)
            file.save(save_path)
            return f"/static/uploads/{filename}"
    except Exception as error:
        print(f"Error uploading image: {error}")
    return None


# ==============================================================================
# Database Product Helpers
# ==============================================================================

def format_product(p):
    if not p:
        return None
    image_url = p.thumbnail
    if not image_url and p.images:
        image_url = p.images[0].name
    if not image_url:
        image_url = DEFAULT_PRODUCT_IMAGE

    cat_name = p.category.name if p.category else "General"

    # Collect all images (thumbnail + all gallery images in ProductImage)
    gallery = []
    if p.thumbnail:
        gallery.append(p.thumbnail)
    for img in p.images:
        if img.name and img.name not in gallery:
            gallery.append(img.name)
    if not gallery:
        gallery = [image_url]

    return {
        "id": p.id,
        "name": p.name,
        "title": p.name,
        "thumbnail": p.thumbnail,
        "image": image_url,
        "images": gallery,
        "gallery": gallery,
        "Cost": float(p.Cost) if p.Cost is not None else 0.0,
        "cost": float(p.Cost) if p.Cost is not None else 0.0,
        "Price": float(p.Price) if p.Price is not None else 0.0,
        "price": float(p.Price) if p.Price is not None else 0.0,
        "Stock": p.Stock or 0,
        "stock": p.Stock or 0,
        "CategoryId": p.CategoryId,
        "category_id": p.CategoryId,
        "category": cat_name,
        "description": p.description or "",
        "rating": {"rate": 4.8, "count": 25},
    }


def get_products():
    try:
        products = Product.query.order_by(Product.id.asc()).all()
        return [format_product(p) for p in products]
    except Exception as error:
        print(f"Error fetching products from database: {error}")
        return []


def get_product(product_id):
    try:
        product = Product.query.get(product_id)
        if product:
            return decorate_product(format_product(product))
        return None
    except Exception as error:
        print(f"Error fetching product {product_id} from database: {error}")
        return None


def decorate_product(product):
    if not product:
        return product

    product = dict(product)
    discounted_price = float(product["price"])
    product["discounted_price"] = discounted_price
    product["original_price"] = round(discounted_price * 1.15, 2)
    product["has_discount"] = product["original_price"] > product["discounted_price"]
    return product


def decorate_products(products):
    return [decorate_product(product) for product in products]


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    with open(USERS_FILE, encoding="utf-8") as users_file:
        try:
            return json.load(users_file)
        except json.JSONDecodeError:
            return {}


def save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as users_file:
        json.dump(users, users_file, indent=2)


def hash_password(password):
    return generate_password_hash(password)


def check_password(password, stored_password):
    if not stored_password or not password:
        return False
    try:
        if check_password_hash(stored_password, password):
            return True
    except Exception:
        pass

    # Backward compatibility with legacy custom salt$hash
    try:
        if "$" in stored_password:
            salt, digest = stored_password.split("$", 1)
            if hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest() == digest:
                return True
    except Exception:
        pass

    return False


def get_cart():
    raw_cart = request.cookies.get(CART_COOKIE, "{}")
    try:
        cart = json.loads(raw_cart)
    except json.JSONDecodeError:
        return {}

    clean_cart = {}
    for product_id, quantity in cart.items():
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if quantity > 0:
            clean_cart[str(product_id)] = quantity

    return clean_cart


def redirect_with_cart(location, cart):
    response = make_response(redirect(location))
    if cart:
        response.set_cookie(
            CART_COOKIE,
            json.dumps(cart, separators=(",", ":")),
            max_age=CART_MAX_AGE,
            samesite="Lax",
        )
    else:
        response.delete_cookie(CART_COOKIE)
    return response


def cart_count():
    return sum(get_cart().values())


def build_cart_items():
    items = []
    total = 0

    for product_id, quantity in get_cart().items():
        product = get_product(product_id)
        if not product:
            continue

        subtotal = float(product["discounted_price"]) * int(quantity)
        total += subtotal
        items.append({"product": product, "quantity": int(quantity), "subtotal": subtotal})

    return items, total


def get_admin_users_list():
    db_users = User.query.order_by(User.id.desc()).all()
    users = []
    for u in db_users:
        initials = "".join([part[0].upper() for part in (u.fullname or u.email).split()[:2]]) or "U"
        joined_str = u.create_at.strftime("%b %d, %Y") if u.create_at else "Jan 15, 2026"
        users.append({
            "id": u.id,
            "image": u.image,
            "name": u.fullname or u.email.split("@")[0],
            "email": u.email,
            "password": u.password,
            "role": u.role,
            "status": u.status,
            "joined": joined_str,
            "avatar": initials,
        })
    return users


def send_checkout_notification(name, phone, email, address, notes, items, total):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not has_telegram_config(bot_token, chat_id):
        if current_app:
            current_app.logger.info("Telegram notification skipped because credentials are missing.")
        return

    lines = [
        "New checkout order",
        f"Name: {name}",
        f"Phone: {phone}",
        f"Email: {email}",
        f"Address: {address}",
        f"Notes: {notes or '-'}",
        "",
        "Items:",
    ]

    for item in items:
        product = item["product"]
        lines.append(
            f"- {product['title']} x {item['quantity']} = ${item['subtotal']:.2f}"
        )

    lines.append(f"Total: ${total:.2f}")

    try:
        payload = json.dumps({"chat_id": chat_id, "text": "\n".join(lines)}).encode("utf-8")
        telegram_request = urllib_request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib_request.urlopen(telegram_request, timeout=10).read()
    except (URLError, TimeoutError) as exc:
        if current_app:
            current_app.logger.warning("Telegram notification failed: %s", exc)


def has_telegram_config(bot_token, chat_id):
    missing_values = {"", "YOUR_BOT_TOKEN_HERE", "YOUR_GROUP_CHAT_ID_HERE"}
    return (bot_token or "") not in missing_values and (chat_id or "") not in missing_values

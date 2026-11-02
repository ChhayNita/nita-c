from datetime import datetime
from extensions import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    customer_name = db.Column(db.String(128), nullable=False)
    customer_phone = db.Column(db.String(64), nullable=False)
    customer_email = db.Column(db.String(128), nullable=True)

    delivery_type = db.Column(db.String(32), nullable=False, default="delivery")  # 'delivery' or 'pickup'
    shipping_address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    payment_method = db.Column(db.String(32), nullable=False, default="khqr")     # 'khqr', 'cash'
    payment_status = db.Column(db.String(32), nullable=False, default="Paid")      # 'Paid', 'Pending', 'Failed'
    order_status = db.Column(db.String(32), nullable=False, default="Processing")  # 'Processing', 'Delivered', 'Picked Up', 'Completed', 'Cancelled'

    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    currency = db.Column(db.String(10), default="USD")

    # Bakong payment tracking fields
    bakong_md5 = db.Column(db.String(64), nullable=True, index=True)
    bakong_qr = db.Column(db.Text, nullable=True)
    bakong_hash = db.Column(db.String(128), nullable=True)

    create_at = db.Column(db.DateTime, default=datetime.utcnow)
    update_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan", lazy=True)
    user = db.relationship('User', backref='orders', lazy=True)

    def __repr__(self):
        return f"<Order {self.order_number}>"


from sqlalchemy.orm import synonym


class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    product_name = db.Column(db.String(255), nullable=False)
    product_image = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    product_price = synonym('price')
    product = db.relationship('Product', lazy=True)

    def __repr__(self):
        return f"<OrderItem {self.product_name} x {self.quantity}>"


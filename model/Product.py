from extensions import db
from sqlalchemy.orm import synonym


DEFAULT_PRODUCT_IMAGE = "https://arthurmillerfoundation.org/wp-content/uploads/2018/06/default-placeholder.png"


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True, default=DEFAULT_PRODUCT_IMAGE)
    Cost = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    Price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    Stock = db.Column(db.Integer, nullable=False, default=0)
    CategoryId = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Synonyms for standard Python lowercase attribute access
    cost = synonym('Cost')
    price = synonym('Price')
    stock = synonym('Stock')
    category_id = synonym('CategoryId')

    # Relationship to ProductImage
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.name}>"

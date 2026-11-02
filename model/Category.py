from extensions import db


DEFAULT_CATEGORY_IMAGE = "https://arthurmillerfoundation.org/wp-content/uploads/2018/06/default-placeholder.png"


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=True, default=DEFAULT_CATEGORY_IMAGE)
    description = db.Column(db.Text, nullable=True)

    # Relationship to Product
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"

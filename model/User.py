from datetime import datetime
from extensions import db


DEFAULT_PROFILE_IMAGE = "https://arthurmillerfoundation.org/wp-content/uploads/2018/06/default-placeholder.png"


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Text, nullable=True)
    fullname = db.Column(db.String(128))
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="Customer")
    status = db.Column(db.String(30), nullable=False, default="Active")
    create_at = db.Column(db.DateTime, default=datetime.utcnow)
    update_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def name(self):
        return self.fullname or (self.email.split('@')[0] if self.email else 'User')

    @property
    def profile_image(self):
        return self.image or DEFAULT_PROFILE_IMAGE

    @property
    def avatar(self):
        if self.fullname:
            parts = self.fullname.split()
            return "".join([p[0].upper() for p in parts[:2]])
        return "U"

    def __repr__(self):
        return f"<User {self.email}>"

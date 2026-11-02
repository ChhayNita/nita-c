from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Import route modules so decorators attach to admin_bp
from . import auth
from . import dashboard
from . import products
from . import users
from . import categories
from . import orders
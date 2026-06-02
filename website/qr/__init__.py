from flask import Blueprint

qr_bp = Blueprint('qr', __name__, template_folder='../templates/qr')

from . import routes  # noqa: E402, F401

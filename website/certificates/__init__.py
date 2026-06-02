from flask import Blueprint

certificates_bp = Blueprint('certificates', __name__, template_folder='../templates/certificates')

from . import routes  # noqa: E402, F401

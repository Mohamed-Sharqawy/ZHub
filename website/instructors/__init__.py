from flask import Blueprint

instructors_bp = Blueprint('instructors', __name__, template_folder='../templates/instructors')

from . import routes  # noqa: E402, F401

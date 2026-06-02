from flask import Blueprint

courses_bp = Blueprint('courses', __name__, template_folder='../templates/courses')

from . import routes  # noqa: E402, F401

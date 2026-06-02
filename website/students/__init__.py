from flask import Blueprint

students_bp = Blueprint('students', __name__, template_folder='../templates/students')

from . import routes  # noqa: E402, F401

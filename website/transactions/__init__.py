from flask import Blueprint

transactions_bp = Blueprint('transactions', __name__, template_folder='../templates/transactions')

from . import routes  # noqa: E402, F401

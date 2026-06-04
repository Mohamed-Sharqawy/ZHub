from datetime import date as _date

from flask_wtf import FlaskForm
from wtforms import (SelectField, FloatField, TextAreaField,
                     StringField, DateField, SubmitField)
from wtforms.validators import DataRequired, Optional, NumberRange, Length


class TransactionForm(FlaskForm):
    """Single form that handles both income and expense transactions.

    Fields are selectively required depending on transaction_kind.
    Server-side validation in the route enforces the rules because
    all income/expense-specific fields are marked Optional here
    (only transaction_kind and date are unconditionally required).
    """

    # ── Classification ──────────────────────────────────────────────────────
    transaction_kind = SelectField(
        'Transaction Type',
        choices=[
            ('income',  'Income — Student Payment'),
            ('expense', 'Expense — Operational Cost'),
        ],
        validators=[DataRequired()],
    )

    # ── Income-only fields ──────────────────────────────────────────────────
    student_id = SelectField(
        'Student',
        coerce=int,
        validators=[Optional()],
    )
    course_id = SelectField(
        'Course',
        coerce=int,
        validators=[Optional()],
    )
    payment_type = SelectField(
        'Payment Category',
        choices=[
            ('',            '— Select category —'),
            ('reservation', 'Reservation Fee'),
            ('course',      'Course Fee'),
            ('certificate', 'Certificate Fee'),
        ],
        validators=[Optional()],
    )
    total_amount = FloatField(
        'Total Amount Due (EGP)',
        validators=[Optional(), NumberRange(min=0,
                    message='Total amount must be zero or more.')],
    )
    paid_amount = FloatField(
        'Amount Received This Payment (EGP)',
        validators=[Optional(), NumberRange(min=0,
                    message='Amount received must be zero or more.')],
    )

    # ── Expense-only fields ─────────────────────────────────────────────────
    expense_category = SelectField(
        'Expense Category',
        choices=[
            ('',             '— Select category —'),
            ('electricity',  'Electricity Bill'),
            ('water',        'Water Bill'),
            ('gas',          'Gas Bill'),
            ('rent',         'Rent'),
            ('maintenance',  'Maintenance'),
            ('other',        'Other'),
        ],
        validators=[Optional()],
    )
    expense_description = StringField(
        'Describe the Expense (required when "Other" is selected)',
        validators=[Optional(), Length(max=500)],
    )
    expense_amount = FloatField(
        'Amount Paid (EGP)',
        validators=[Optional(), NumberRange(min=0,
                    message='Amount must be zero or more.')],
    )

    # ── Common fields ───────────────────────────────────────────────────────
    date = DateField(
        'Transaction Date',
        validators=[DataRequired()],
        default=_date.today,
    )
    notes = TextAreaField(
        'Notes (optional)',
        validators=[Optional()],
    )
    submit = SubmitField('Save Transaction')

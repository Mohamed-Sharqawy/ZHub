from datetime import datetime, time, timezone

from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from sqlalchemy import func

from . import transactions_bp
from .forms import TransactionForm
from ..extensions import db
from ..models import Transaction, Student, Course
from ..utils import role_required


# ─────────────────────────────────────────────────────────────────────────────
# LIST ALL TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────────────

@transactions_bp.route('/')
@role_required('admin')
def list_transactions():
    # Read the kind filter from the URL query string.
    # Valid values: 'income', 'expense', 'all' (default).
    # request.args reads from the URL query string only (GET parameters).
    kind_filter = request.args.get('kind', 'all').strip().lower()

    # Guard: if the value is not one of the three valid options, reset to 'all'
    if kind_filter not in ('income', 'expense', 'all'):
        kind_filter = 'all'

    # Build the base query
    base_query = Transaction.query

    # Apply the kind filter at the database level before executing
    if kind_filter == 'income':
        base_query = base_query.filter(
            Transaction.transaction_kind == 'income'
        )
    elif kind_filter == 'expense':
        base_query = base_query.filter(
            Transaction.transaction_kind == 'expense'
        )
    # If kind_filter == 'all', no filter is applied — all records returned

    # Execute the query, ordered by most recent date first
    transactions = base_query.order_by(Transaction.date.desc()).all()

    # Compute summary totals always across ALL records (not filtered)
    # so the cards always show the full picture regardless of filter
    total_income = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_kind == 'income'
    ).scalar() or 0.0

    total_expense = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_kind == 'expense'
    ).scalar() or 0.0

    net_balance = total_income - total_expense

    return render_template(
        'transactions/list.html',
        transactions=transactions,
        kind_filter=kind_filter,
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,
    )


# ─────────────────────────────────────────────────────────────────────────────
# RECORD A NEW TRANSACTION
# ─────────────────────────────────────────────────────────────────────────────

@transactions_bp.route('/record', methods=['GET', 'POST'])
@role_required('admin')
def record_transaction():
    form = TransactionForm()

    # Populate dynamic choices
    students = Student.query.join(Student.user).order_by(
        Student.id.asc()).all()
    form.student_id.choices = [(0, '— Select student —')] + [
        (s.id, s.user.full_name) for s in students
    ]
    courses = Course.query.filter_by(is_active=True).order_by(
        Course.name.asc()).all()
    form.course_id.choices = [(0, '— Select course —')] + [
        (c.id, c.name) for c in courses
    ]

    if form.validate_on_submit():
        kind = form.transaction_kind.data

        # ── SERVER-SIDE VALIDATION ──────────────────────────────────────────

        if kind == 'income':
            errors = []
            if not form.student_id.data or form.student_id.data == 0:
                errors.append('Student is required for income transactions.')
            if not form.course_id.data or form.course_id.data == 0:
                errors.append('Course is required for income transactions.')
            if not form.payment_type.data:
                errors.append('Payment category is required for income transactions.')
            if form.total_amount.data is None:
                errors.append('Total amount due is required for income transactions.')
            if form.paid_amount.data is None:
                errors.append('Amount received is required for income transactions.')
            if (form.total_amount.data is not None and
                    form.paid_amount.data is not None and
                    form.paid_amount.data > form.total_amount.data):
                errors.append(
                    'Amount received cannot exceed the total amount due.'
                )
            for err in errors:
                flash(err, 'danger')
            if errors:
                return render_template('transactions/record.html', form=form)

            transaction = Transaction(
                transaction_kind = 'income',
                student_id       = form.student_id.data,
                course_id        = form.course_id.data,
                payment_type     = form.payment_type.data,
                total_amount     = form.total_amount.data,
                paid_amount      = form.paid_amount.data,
                amount           = form.paid_amount.data,
                date             = datetime.combine(
                                         form.date.data,
                                         time(0, 0),
                                         tzinfo=timezone.utc,
                                     ),
                recorded_by      = current_user.id,
                notes            = form.notes.data or None,
            )

        elif kind == 'expense':
            errors = []
            if not form.expense_category.data:
                errors.append('Expense category is required.')
            if (form.expense_category.data == 'other' and
                    not form.expense_description.data):
                errors.append(
                    'Please describe the expense when "Other" is selected.'
                )
            if form.expense_amount.data is None:
                errors.append('Amount paid is required for expense transactions.')
            for err in errors:
                flash(err, 'danger')
            if errors:
                return render_template('transactions/record.html', form=form)

            transaction = Transaction(
                transaction_kind    = 'expense',
                expense_category    = form.expense_category.data,
                expense_description = (form.expense_description.data
                                         if form.expense_category.data == 'other'
                                         else None),
                amount              = form.expense_amount.data,
                date                = datetime.combine(
                                            form.date.data,
                                            time(0, 0),
                                            tzinfo=timezone.utc,
                                        ),
                recorded_by         = current_user.id,
                notes               = form.notes.data or None,
            )

        else:
            flash('Invalid transaction type.', 'danger')
            return render_template('transactions/record.html', form=form)

        db.session.add(transaction)
        db.session.commit()
        flash('Transaction recorded successfully.', 'success')
        return redirect(url_for('transactions.list_transactions'))

    return render_template('transactions/record.html', form=form)


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT TRANSACTION HISTORY (income only)
# ─────────────────────────────────────────────────────────────────────────────

@transactions_bp.route('/student/<int:student_id>')
@role_required('admin', 'student')
def student_transactions(student_id):
    student = Student.query.get_or_404(student_id)

    if current_user.role == 'student':
        if not current_user.student or current_user.student.id != student_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.home'))

    income_records = (
        student.transactions
        .filter_by(transaction_kind='income')
        .order_by(Transaction.date.desc())
        .all()
    )

    total_paid = sum(t.paid_amount or 0.0 for t in income_records)
    total_due  = sum(t.total_amount or 0.0 for t in income_records)
    total_remaining = sum(t.remaining_amount for t in income_records)

    return render_template(
        'transactions/student.html',
        student=student,
        income_records=income_records,
        total_paid=total_paid,
        total_due=total_due,
        total_remaining=total_remaining,
    )

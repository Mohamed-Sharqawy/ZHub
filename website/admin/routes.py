import json
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from sqlalchemy import func

from . import admin_bp
from .forms import UserCreateForm
from ..extensions import db
from ..models import (
    User, Student, Instructor, Course, Enrollment, Transaction,
    Attendance, Certificate, Group, Assignment
)
from ..students.forms import AssignmentForm
from ..utils import role_required


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_kind == 'income'
    ).scalar() or 0
    total_expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_kind == 'expense'
    ).scalar() or 0
    stats = {
        'total_students': Student.query.count(),
        'total_instructors': Instructor.query.count(),
        'total_courses': Course.query.filter_by(is_active=True).count(),
        'total_enrollments': Enrollment.query.filter_by(status='active').count(),
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': total_income - total_expenses,
        'total_certificates': Certificate.query.count(),
    }
    # Recent enrollments
    recent_enrollments = Enrollment.query.order_by(Enrollment.enrolled_at.desc()).limit(5).all()
    # Recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(5).all()

    return render_template('admin/dashboard.html', stats=stats,
                           recent_enrollments=recent_enrollments,
                           recent_transactions=recent_transactions)


@admin_bp.route('/users')
@role_required('admin')
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users/list.html', users=users)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@role_required('admin')
def create_user():
    form = UserCreateForm()
    if form.validate_on_submit():
        role = form.role.data

        # ── Email: required for admin and instructor, optional for student ──
        if role in ('admin', 'instructor') and not form.email.data:
            flash('Email is required for admin and instructor accounts.', 'danger')
            return render_template('admin/users/create.html', form=form)

        # ── Email uniqueness check (only when an email was provided) ────────
        if form.email.data:
            if User.query.filter_by(email=form.email.data).first():
                flash('A user with this email already exists.', 'danger')
                return render_template('admin/users/create.html', form=form)

        # ── School and grade: mandatory for student accounts ─────────────────
        if role == 'student':
            if not form.school_name.data or not form.school_name.data.strip():
                flash('School name is required for student accounts.', 'danger')
                return render_template('admin/users/create.html', form=form)
            if not form.grade.data or not form.grade.data.strip():
                flash('Grade / Year is required for student accounts.', 'danger')
                return render_template('admin/users/create.html', form=form)

        # ── Create User record ───────────────────────────────────────────────
        # email is stored as NULL (not empty string) when not provided.
        user = User(
            email=form.email.data or None,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=role,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Obtain user.id before creating child record

        if role == 'student':
            student = Student(
                user_id=user.id,
                date_of_birth=form.date_of_birth.data,
                guardian_phone=form.guardian_phone.data,
                notes=form.notes.data,
                school_name=form.school_name.data.strip(),
                grade=form.grade.data.strip(),
            )
            db.session.add(student)
        elif role == 'instructor':
            instructor = Instructor(
                user_id=user.id,
                specialization=form.specialization.data,
                bio=form.bio.data,
            )
            db.session.add(instructor)

        db.session.commit()
        flash(f'User {user.full_name} ({role}) created successfully.', 'success')
        return redirect(url_for('admin.list_users'))

    return render_template('admin/users/create.html', form=form)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@role_required('admin')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.list_users'))

    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/reports/transactions')
@role_required('admin')
def report_transactions():
    # ── Parse filter parameters from URL query string (GET only) ───────
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str   = request.args.get('date_to',   '').strip()
    kind_filter   = request.args.get('kind', 'all').strip().lower()
    ptype_filter  = request.args.get('payment_type', 'all').strip().lower()
    ecat_filter   = request.args.get('expense_category', 'all').strip().lower()

    # Guard invalid kind values
    if kind_filter not in ('all', 'income', 'expense'):
        kind_filter = 'all'

    # Parse date strings into datetime objects
    from datetime import datetime as _dt
    date_from_dt = None
    date_to_dt   = None
    try:
        if date_from_str:
            date_from_dt = _dt.strptime(date_from_str, '%Y-%m-%d')
    except ValueError:
        date_from_str = ''
    try:
        if date_to_str:
            date_to_dt = _dt.strptime(date_to_str, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59)
    except ValueError:
        date_to_str = ''

    # ── SUMMARY CARDS — always computed over ALL records, no filters ────
    # Card 1: Total Income Received (actual money received from students)
    total_income_received = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_kind == 'income'
    ).scalar() or 0.0

    # For outstanding: need sum of total_amount and sum of paid_amount
    total_income_due = db.session.query(
        func.sum(Transaction.total_amount)
    ).filter(
        Transaction.transaction_kind == 'income',
        Transaction.total_amount.isnot(None)
    ).scalar() or 0.0

    total_income_paid_sum = db.session.query(
        func.sum(Transaction.paid_amount)
    ).filter(
        Transaction.transaction_kind == 'income',
        Transaction.paid_amount.isnot(None)
    ).scalar() or 0.0

    # Card 3: Outstanding = what students still owe
    total_remaining = round(max(0.0, total_income_due - total_income_paid_sum), 2)

    # Card 2: Total Expenses
    total_expenses = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_kind == 'expense'
    ).scalar() or 0.0

    # Card 4: Net Balance = income received minus expenses
    # Outstanding installments do NOT reduce this number
    net_balance = round(total_income_received - total_expenses, 2)

    # ── CHART DATA — always computed over ALL records, no filters ────────

    # Chart 1: Monthly Income vs Expenses
    monthly_income_rows = db.session.query(
        func.strftime('%Y-%m', Transaction.date).label('month'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.transaction_kind == 'income'
    ).group_by('month').order_by('month').all()

    monthly_expense_rows = db.session.query(
        func.strftime('%Y-%m', Transaction.date).label('month'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.transaction_kind == 'expense'
    ).group_by('month').order_by('month').all()

    all_months = sorted(set(
        [r.month for r in monthly_income_rows] +
        [r.month for r in monthly_expense_rows]
    ))
    income_by_month  = {r.month: float(r.total) for r in monthly_income_rows}
    expense_by_month = {r.month: float(r.total) for r in monthly_expense_rows}
    chart_months         = json.dumps(all_months)
    chart_income_values  = json.dumps([income_by_month.get(m, 0.0)  for m in all_months])
    chart_expense_values = json.dumps([expense_by_month.get(m, 0.0) for m in all_months])

    # Chart 3: Expenses by category
    expense_cat_rows = db.session.query(
        Transaction.expense_category,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.transaction_kind == 'expense',
        Transaction.expense_category.isnot(None)
    ).group_by(Transaction.expense_category).all()

    EXPENSE_LABELS = {
        'electricity': 'Electricity', 'water': 'Water',
        'gas': 'Gas', 'rent': 'Rent',
        'maintenance': 'Maintenance', 'other': 'Other',
    }
    chart_expense_cat_labels = json.dumps([
        EXPENSE_LABELS.get(r.expense_category, r.expense_category)
        for r in expense_cat_rows
    ])
    chart_expense_cat_values = json.dumps([float(r.total) for r in expense_cat_rows])
    has_expense_cat_data = len(expense_cat_rows) > 0

    # Chart 4: Income by payment type
    income_type_rows = db.session.query(
        Transaction.payment_type,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.transaction_kind == 'income',
        Transaction.payment_type.isnot(None)
    ).group_by(Transaction.payment_type).all()

    PAYMENT_LABELS = {
        'reservation': 'Reservation Fee',
        'course': 'Course Fee',
        'certificate': 'Certificate Fee',
    }
    chart_income_type_labels = json.dumps([
        PAYMENT_LABELS.get(r.payment_type, r.payment_type)
        for r in income_type_rows
    ])
    chart_income_type_values = json.dumps([float(r.total) for r in income_type_rows])
    has_income_type_data = len(income_type_rows) > 0

    # ── FILTERED TRANSACTION TABLE ────────────────────────────────────────
    tq = Transaction.query

    if date_from_dt:
        tq = tq.filter(Transaction.date >= date_from_dt)
    if date_to_dt:
        tq = tq.filter(Transaction.date <= date_to_dt)
    if kind_filter == 'income':
        tq = tq.filter(Transaction.transaction_kind == 'income')
        valid_ptypes = ('reservation', 'course', 'certificate')
        if ptype_filter != 'all' and ptype_filter in valid_ptypes:
            tq = tq.filter(Transaction.payment_type == ptype_filter)
    elif kind_filter == 'expense':
        tq = tq.filter(Transaction.transaction_kind == 'expense')
        valid_ecats = ('electricity', 'water', 'gas', 'rent', 'maintenance', 'other')
        if ecat_filter != 'all' and ecat_filter in valid_ecats:
            tq = tq.filter(Transaction.expense_category == ecat_filter)

    transactions = tq.order_by(Transaction.date.desc()).all()

    return render_template(
        'admin/reports/transactions.html',
        # Summary cards
        total_income_received = round(total_income_received, 2),
        total_expenses        = round(total_expenses, 2),
        total_remaining       = total_remaining,
        net_balance           = net_balance,
        # Chart data (JSON strings, use | safe in template)
        chart_months              = chart_months,
        chart_income_values       = chart_income_values,
        chart_expense_values      = chart_expense_values,
        chart_expense_cat_labels  = chart_expense_cat_labels,
        chart_expense_cat_values  = chart_expense_cat_values,
        chart_income_type_labels  = chart_income_type_labels,
        chart_income_type_values  = chart_income_type_values,
        has_expense_cat_data      = has_expense_cat_data,
        has_income_type_data      = has_income_type_data,
        # Filtered table
        transactions   = transactions,
        # Filter state (for repopulating form controls)
        date_from_str  = date_from_str,
        date_to_str    = date_to_str,
        kind_filter    = kind_filter,
        ptype_filter   = ptype_filter,
        ecat_filter    = ecat_filter,
    )


@admin_bp.route('/reports/attendance')
@role_required('admin')
def report_attendance():
    # ── Parse filter parameters ─────────────────────────────────────────
    course_filter     = request.args.get('course_id',     'all').strip()
    instructor_filter = request.args.get('instructor_id', 'all').strip()

    # ── Build filtered group list ───────────────────────────────────────
    groups_query = Group.query.filter_by(is_active=True)

    if course_filter != 'all':
        try:
            groups_query = groups_query.filter_by(course_id=int(course_filter))
        except (ValueError, TypeError):
            course_filter = 'all'

    if instructor_filter != 'all':
        try:
            groups_query = groups_query.filter_by(instructor_id=int(instructor_filter))
        except (ValueError, TypeError):
            instructor_filter = 'all'

    groups = groups_query.all()

    # ── Build per-group stats ───────────────────────────────────────────
    report_data = []
    for group in groups:
        total_records = Attendance.query.filter_by(group_id=group.id).count()
        present       = Attendance.query.filter_by(group_id=group.id, status='present').count()
        absent        = total_records - present
        rate          = round((present / total_records * 100), 1) if total_records > 0 else 0
        report_data.append({
            'group':         group,
            'total_records': total_records,
            'present':       present,
            'absent':        absent,
            'rate':          rate,
        })

    # Sort ascending by rate (worst performers first)
    report_data.sort(key=lambda x: x['rate'])

    # ── Overall summary stats ───────────────────────────────────────────
    total_present     = sum(r['present']       for r in report_data)
    total_absent      = sum(r['absent']         for r in report_data)
    total_records_all = sum(r['total_records'] for r in report_data)
    overall_rate      = round((total_present / total_records_all * 100), 1) \
                        if total_records_all > 0 else 0

    # ── Chart data ──────────────────────────────────────────────────────
    # Chart 1: Overall doughnut [present, absent]
    chart_overall_data = json.dumps([total_present, total_absent])

    # Chart 2: Per-group horizontal bar
    chart_group_labels = json.dumps([
        f"{r['group'].course.name} — {r['group'].name}"
        for r in report_data
    ])
    chart_group_rates = json.dumps([r['rate'] for r in report_data])
    chart_group_colors = json.dumps([
        'rgba(25, 135, 84, 0.8)'  if r['rate'] >= 75 else
        ('rgba(255, 193, 7, 0.8)' if r['rate'] >= 50 else
         'rgba(220, 53, 69, 0.8)')
        for r in report_data
    ])

    # ── Filter dropdown data ────────────────────────────────────────────
    all_courses     = Course.query.filter_by(is_active=True).order_by(Course.name).all()
    all_instructors = Instructor.query.join(Instructor.user).order_by(Instructor.id).all()

    return render_template(
        'admin/reports/attendance.html',
        report_data       = report_data,
        # Summary cards
        overall_rate      = overall_rate,
        total_present     = total_present,
        total_absent      = total_absent,
        total_records_all = total_records_all,
        # Chart data (JSON strings, use | safe in template)
        chart_overall_data  = chart_overall_data,
        chart_group_labels  = chart_group_labels,
        chart_group_rates   = chart_group_rates,
        chart_group_colors  = chart_group_colors,
        # Filter dropdowns
        all_courses         = all_courses,
        all_instructors     = all_instructors,
        # Filter state
        course_filter       = course_filter,
        instructor_filter   = instructor_filter,
    )


@admin_bp.route('/assignments/create', methods=['GET', 'POST'])
@role_required('admin')
def create_assignment():
    form = AssignmentForm()
    courses = Course.query.filter_by(is_active=True).all()
    form.course_id.choices = [(c.id, c.name) for c in courses]

    if form.validate_on_submit():
        assignment = Assignment(
            course_id=form.course_id.data,
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            created_by=current_user.id
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment created successfully.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/assignments/create.html', form=form)

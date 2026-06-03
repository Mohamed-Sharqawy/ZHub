from flask import render_template, redirect, url_for, flash
from flask_login import current_user
from sqlalchemy import func

from . import admin_bp
from .forms import UserCreateForm
from ..extensions import db
from ..models import (
    User, Student, Instructor, Course, Enrollment, Payment,
    Attendance, Certificate, Group, Assignment
)
from ..students.forms import AssignmentForm
from ..utils import role_required


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    stats = {
        'total_students': Student.query.count(),
        'total_instructors': Instructor.query.count(),
        'total_courses': Course.query.filter_by(is_active=True).count(),
        'total_enrollments': Enrollment.query.filter_by(status='active').count(),
        'total_revenue': db.session.query(func.sum(Payment.amount)).scalar() or 0,
        'total_certificates': Certificate.query.count(),
    }
    # Recent enrollments
    recent_enrollments = Enrollment.query.order_by(Enrollment.enrolled_at.desc()).limit(5).all()
    # Recent payments
    recent_payments = Payment.query.order_by(Payment.paid_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html', stats=stats,
                           recent_enrollments=recent_enrollments,
                           recent_payments=recent_payments)


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
        # Check unique email
        if User.query.filter_by(email=form.email.data).first():
            flash('A user with this email already exists.', 'danger')
            return render_template('admin/users/create.html', form=form)

        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Get user.id before creating child record

        if form.role.data == 'student':
            student = Student(
                user_id=user.id,
                date_of_birth=form.date_of_birth.data,
                guardian_phone=form.guardian_phone.data,
                notes=form.notes.data,
            )
            db.session.add(student)
        elif form.role.data == 'instructor':
            instructor = Instructor(
                user_id=user.id,
                specialization=form.specialization.data,
                bio=form.bio.data,
            )
            db.session.add(instructor)

        db.session.commit()
        flash(f'User {user.full_name} ({user.role}) created successfully.', 'success')
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


@admin_bp.route('/reports/payments')
@role_required('admin')
def report_payments():
    payments = Payment.query.order_by(Payment.paid_at.desc()).all()
    total = db.session.query(func.sum(Payment.amount)).scalar() or 0
    return render_template('admin/reports/payments.html', payments=payments, total=total)


@admin_bp.route('/reports/attendance')
@role_required('admin')
def report_attendance():
    groups = Group.query.filter_by(is_active=True).all()
    report_data = []
    for group in groups:
        total_records = Attendance.query.filter_by(group_id=group.id).count()
        present = Attendance.query.filter_by(group_id=group.id, status='present').count()
        rate = round((present / total_records * 100), 1) if total_records > 0 else 0
        report_data.append({
            'group': group,
            'total_records': total_records,
            'present': present,
            'rate': rate,
        })
    return render_template('admin/reports/attendance.html', report_data=report_data)


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
    return render_template('admin/assignment_form.html', form=form)

from flask import render_template, redirect, url_for, flash
from flask_login import current_user

from . import payments_bp
from .forms import PaymentForm
from ..extensions import db
from ..models import Payment, Student, Course
from ..utils import role_required


@payments_bp.route('/')
@role_required('admin')
def list_payments():
    payments = Payment.query.order_by(Payment.paid_at.desc()).all()
    return render_template('payments/list.html', payments=payments)


@payments_bp.route('/student/<int:student_id>')
@role_required('admin', 'student')
def student_payments(student_id):
    student = Student.query.get_or_404(student_id)
    if current_user.role == 'student':
        if not current_user.student or current_user.student.id != student_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.home'))

    payments = student.payments.order_by(Payment.paid_at.desc()).all()
    return render_template('payments/student.html', student=student, payments=payments)


@payments_bp.route('/record', methods=['GET', 'POST'])
@role_required('admin')
def record_payment():
    form = PaymentForm()
    students = Student.query.join(Student.user).all()
    form.student_id.choices = [(s.id, s.user.full_name) for s in students]
    courses = Course.query.filter_by(is_active=True).all()
    form.course_id.choices = [(c.id, c.name) for c in courses]

    if form.validate_on_submit():
        payment = Payment(
            student_id=form.student_id.data,
            course_id=form.course_id.data,
            payment_type=form.payment_type.data,
            amount=form.amount.data,
            received_by=current_user.id,
            notes=form.notes.data,
        )
        db.session.add(payment)
        db.session.commit()
        flash('Payment recorded successfully.', 'success')
        return redirect(url_for('payments.list_payments'))

    return render_template('payments/record.html', form=form)

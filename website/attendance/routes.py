from datetime import date, datetime

from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user

from . import attendance_bp
from ..extensions import db
from ..models import Group, Enrollment, Attendance
from ..utils import role_required, get_attendance_percentage


def _parse_date(date_str):
    """Parse a date string (YYYY-MM-DD) to a Python date object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return date.today()


@attendance_bp.route('/group/<int:group_id>')
@role_required('admin', 'instructor')
def group_sheet(group_id):
    group = Group.query.get_or_404(group_id)
    # Only the assigned instructor or admin can view
    if current_user.role == 'instructor':
        if not current_user.instructor or current_user.instructor.id != group.instructor_id:
            flash('You are not assigned to this group.', 'danger')
            return redirect(url_for('auth.home'))

    enrollments = group.enrollments.filter_by(status='active').all()
    selected_date_str = request.args.get('date', date.today().isoformat())
    selected_date = _parse_date(selected_date_str)

    # Get existing attendance records for this date
    existing = {}
    for record in Attendance.query.filter_by(group_id=group.id, date=selected_date).all():
        existing[record.enrollment_id] = record.status

    return render_template(
        'attendance/sheet.html',
        group=group,
        enrollments=enrollments,
        selected_date=selected_date.isoformat(),
        existing=existing,
    )


@attendance_bp.route('/group/<int:group_id>/mark', methods=['POST'])
@role_required('admin', 'instructor')
def mark_attendance(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user.role == 'instructor':
        if not current_user.instructor or current_user.instructor.id != group.instructor_id:
            flash('You are not assigned to this group.', 'danger')
            return redirect(url_for('auth.home'))

    attendance_date_str = request.form.get('date', date.today().isoformat())
    attendance_date = _parse_date(attendance_date_str)
    enrollments = group.enrollments.filter_by(status='active').all()

    for enrollment in enrollments:
        status = request.form.get(f'status_{enrollment.id}', 'absent')
        # Update or create
        record = Attendance.query.filter_by(
            enrollment_id=enrollment.id,
            date=attendance_date
        ).first()
        if record:
            record.status = status
            record.marked_by = current_user.id
        else:
            record = Attendance(
                enrollment_id=enrollment.id,
                group_id=group.id,
                date=attendance_date,
                status=status,
                marked_by=current_user.id,
            )
            db.session.add(record)

    db.session.commit()
    flash(f'Attendance for {attendance_date} saved.', 'success')
    return redirect(url_for('attendance.group_sheet', group_id=group.id, date=attendance_date.isoformat()))


@attendance_bp.route('/student/<int:student_id>')
@role_required('admin', 'instructor', 'student')
def student_summary(student_id):
    from ..models import Student
    student = Student.query.get_or_404(student_id)

    # Students can only view their own
    if current_user.role == 'student':
        if not current_user.student or current_user.student.id != student_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.home'))

    enrollments = student.enrollments.filter_by(status='active').all()
    summary = []
    for enrollment in enrollments:
        summary.append({
            'enrollment': enrollment,
            'course': enrollment.course,
            'group': enrollment.group,
            'percentage': get_attendance_percentage(enrollment),
            'total': enrollment.attendance_records.count(),
            'present': enrollment.attendance_records.filter_by(status='present').count(),
        })

    return render_template('attendance/summary.html', student=student, summary=summary)

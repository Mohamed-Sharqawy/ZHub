from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required


def role_required(*roles):
    """Decorator that restricts access to users with specific roles.

    Usage:
        @role_required('admin')
        @role_required('admin', 'instructor')
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_attendance_percentage(enrollment):
    """Calculate attendance percentage for an enrollment."""
    total = enrollment.attendance_records.count()
    if total == 0:
        return 0.0
    present = enrollment.attendance_records.filter_by(status='present').count()
    return round((present / total) * 100, 1)


def has_paid(student, course, payment_type):
    """Check if a student has made a specific payment for a course."""
    from .models import Payment
    return Payment.query.filter_by(
        student_id=student.id,
        course_id=course.id,
        payment_type=payment_type
    ).first() is not None

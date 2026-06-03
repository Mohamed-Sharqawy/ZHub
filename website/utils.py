from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required

from .extensions import db


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


def compute_scheduled_hours(start_date, end_date, schedule_slots):
    """
    Compute total scheduled hours for a course.

    Parameters
    ----------
    start_date : datetime.date
    end_date   : datetime.date
    schedule_slots : list of objects/dicts each with:
        - .weekday (or ['weekday'])  — full English weekday name string
        - .duration_hours            — float, hours per session on that slot

    Returns
    -------
    float — total hours that would be consumed by the schedule
    """
    from datetime import date

    weekday_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
    total_hours = 0.0

    for slot in schedule_slots:
        weekday_name = getattr(slot, 'weekday', None) or slot.get('weekday')
        duration = getattr(slot, 'duration_hours', None) or slot.get('duration_hours', 0)

        if not weekday_name or duration <= 0:
            continue

        target_weekday_int = weekday_map.get(weekday_name)
        if target_weekday_int is None:
            continue

        count = sum(1 for d in (date.fromordinal(o) for o in range(start_date.toordinal(), end_date.toordinal() + 1)) if d.weekday() == target_weekday_int)
        total_hours += count * duration

    return total_hours


def compute_assignment_completion_rate(student):
    """
    Returns a float 0.0–100.0 representing assignment completion rate.
    Counts all AssignmentSubmission records for this student.
    'delivered' and 'partial' both count as completed.
    Returns 0.0 if no submissions exist.
    """
    from .models import AssignmentSubmission
    total = AssignmentSubmission.query.filter_by(student_id=student.id).count()
    if total == 0:
        return 0.0
    completed = AssignmentSubmission.query.filter(
        AssignmentSubmission.student_id == student.id,
        AssignmentSubmission.status.in_(['delivered', 'partial'])
    ).count()
    return round((completed / total) * 100, 1)


def compute_overall_attendance_rate(student):
    """
    Returns a float 0.0–100.0 representing overall attendance across all enrollments.
    Uses existing Attendance records for all enrollments of this student.
    Returns 0.0 if no records exist.
    """
    from .models import Attendance, Enrollment
    enrollment_ids = [e.id for e in student.enrollments.all()]
    if not enrollment_ids:
        return 0.0
    total = Attendance.query.filter(Attendance.enrollment_id.in_(enrollment_ids)).count()
    if total == 0:
        return 0.0
    present = Attendance.query.filter(
        Attendance.enrollment_id.in_(enrollment_ids),
        Attendance.status == 'present'
    ).count()
    return round((present / total) * 100, 1)


def compute_participation_score(student):
    """
    Returns the average participation_score across all Attendance records
    where participation_score is not null. Returns None if no scores recorded.
    """
    from .models import Attendance, Enrollment
    from sqlalchemy import func
    enrollment_ids = [e.id for e in student.enrollments.all()]
    if not enrollment_ids:
        return None
    result = db.session.query(func.avg(Attendance.participation_score)).filter(
        Attendance.enrollment_id.in_(enrollment_ids),
        Attendance.participation_score.isnot(None)
    ).scalar()
    return round(float(result), 1) if result is not None else None


def compute_project_completion_rate(student):
    """
    Returns a float 0.0–100.0 representing the percentage of portfolio projects
    that have been marked as 'completed' or 'partial'.
    Projects with status 'not_evaluated' are excluded from denominator.
    Returns 0.0 if no evaluated projects exist.
    """
    from .models import StudentProject
    evaluated = StudentProject.query.filter(
        StudentProject.student_id == student.id,
        StudentProject.completion_status != 'not_evaluated'
    ).count()
    if evaluated == 0:
        return 0.0
    completed = StudentProject.query.filter(
        StudentProject.student_id == student.id,
        StudentProject.completion_status.in_(['completed', 'partial'])
    ).count()
    return round((completed / evaluated) * 100, 1)

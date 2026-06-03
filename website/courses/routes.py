from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from datetime import datetime

from . import courses_bp
from .forms import CourseForm, GroupForm, EnrollmentForm
from ..extensions import db
from ..models import Course, Group, Enrollment, Instructor, Student, CourseSchedule
from ..utils import role_required, compute_scheduled_hours


@courses_bp.route('/')
@role_required('admin', 'instructor', 'student')
def list_courses():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('courses/list.html', courses=courses)


@courses_bp.route('/<int:course_id>')
@role_required('admin', 'instructor', 'student')
def detail(course_id):
    course = Course.query.get_or_404(course_id)
    groups = course.groups.filter_by(is_active=True).all()
    return render_template('courses/detail.html', course=course, groups=groups)


@courses_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin')
def create():
    form = CourseForm()
    if form.schedules and len(form.schedules.entries) == 0:
        form.schedules.append_entry()
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        total_hours = form.total_hours.data or 0.0

        if start_date and end_date:
            if start_date > end_date:
                flash('End date must be after start date.', 'danger')
                return render_template('courses/create.html', form=form)

            valid_entries = [e for e in form.schedules.entries if e.start_time.data and e.end_time.data]
            if valid_entries:
                for entry in valid_entries:
                    from datetime import datetime as dt
                    try:
                        start = dt.strptime(entry.start_time.data.strip(), '%H:%M')
                        end = dt.strptime(entry.end_time.data.strip(), '%H:%M')
                        if end <= start:
                            flash(f'Session end time must be after start time for {entry.weekday.data}.', 'danger')
                            return render_template('courses/create.html', form=form)
                    except ValueError:
                        flash(f'Invalid time format for {entry.weekday.data}. Use HH:MM format.', 'danger')
                        return render_template('courses/create.html', form=form)

                slot_dicts = []
                for entry in valid_entries:
                    from datetime import datetime as dt
                    start = dt.strptime(entry.start_time.data.strip(), '%H:%M')
                    end = dt.strptime(entry.end_time.data.strip(), '%H:%M')
                    duration_hours = (end.hour * 60 + end.minute - start.hour * 60 - start.minute) / 60.0
                    slot_dicts.append({'weekday': entry.weekday.data, 'duration_hours': duration_hours})

                computed_total_hours = compute_scheduled_hours(start_date, end_date, slot_dicts)
                if computed_total_hours > total_hours:
                    flash(f'Schedule exceeds total hours cap. Computed: {computed_total_hours:.1f} h, Cap: {total_hours:.1f} h. Please adjust dates, times, or total hours.', 'danger')
                    return render_template('courses/create.html', form=form)

        course = Course(
            name=form.name.data,
            description=form.description.data,
            level=form.level.data,
            duration_weeks=form.duration_weeks.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            total_hours=form.total_hours.data or 0.0,
            num_sessions=form.num_sessions.data,
            reservation_fee=form.reservation_fee.data or 0.0,
            course_fee=form.course_fee.data or 0.0,
            certificate_fee=form.certificate_fee.data or 0.0,
        )
        db.session.add(course)
        db.session.flush()

        for entry in form.schedules.entries:
            if entry.start_time.data and entry.end_time.data:
                sched = CourseSchedule(
                    course_id=course.id,
                    weekday=entry.weekday.data,
                    start_time=entry.start_time.data.strip(),
                    end_time=entry.end_time.data.strip(),
                )
                db.session.add(sched)
        db.session.commit()
        flash(f'Course "{course.name}" created successfully.', 'success')
        return redirect(url_for('courses.detail', course_id=course.id))
    return render_template('courses/create.html', form=form)


@courses_bp.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)

    while len(form.schedules.entries) > 0:
        form.schedules.pop_entry()
    existing_schedules = course.schedules.all()
    if existing_schedules:
        for s in existing_schedules:
            form.schedules.append_entry({'weekday': s.weekday, 'start_time': s.start_time, 'end_time': s.end_time})
    else:
        form.schedules.append_entry()

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        total_hours = form.total_hours.data or 0.0

        if start_date and end_date:
            if start_date > end_date:
                flash('End date must be after start date.', 'danger')
                return render_template('courses/edit.html', form=form, course=course)

            valid_entries = [e for e in form.schedules.entries if e.start_time.data and e.end_time.data]
            if valid_entries:
                for entry in valid_entries:
                    from datetime import datetime as dt
                    try:
                        start = dt.strptime(entry.start_time.data.strip(), '%H:%M')
                        end = dt.strptime(entry.end_time.data.strip(), '%H:%M')
                        if end <= start:
                            flash(f'Session end time must be after start time for {entry.weekday.data}.', 'danger')
                            return render_template('courses/edit.html', form=form, course=course)
                    except ValueError:
                        flash(f'Invalid time format for {entry.weekday.data}. Use HH:MM format.', 'danger')
                        return render_template('courses/edit.html', form=form, course=course)

                slot_dicts = []
                for entry in valid_entries:
                    from datetime import datetime as dt
                    start = dt.strptime(entry.start_time.data.strip(), '%H:%M')
                    end = dt.strptime(entry.end_time.data.strip(), '%H:%M')
                    duration_hours = (end.hour * 60 + end.minute - start.hour * 60 - start.minute) / 60.0
                    slot_dicts.append({'weekday': entry.weekday.data, 'duration_hours': duration_hours})

                computed_total_hours = compute_scheduled_hours(start_date, end_date, slot_dicts)
                if computed_total_hours > total_hours:
                    flash(f'Schedule exceeds total hours cap. Computed: {computed_total_hours:.1f} h, Cap: {total_hours:.1f} h. Please adjust dates, times, or total hours.', 'danger')
                    return render_template('courses/edit.html', form=form, course=course)

        course.name = form.name.data
        course.description = form.description.data
        course.level = form.level.data
        course.duration_weeks = form.duration_weeks.data
        course.reservation_fee = form.reservation_fee.data or 0.0
        course.course_fee = form.course_fee.data or 0.0
        course.certificate_fee = form.certificate_fee.data or 0.0
        course.start_date = form.start_date.data
        course.end_date = form.end_date.data
        course.total_hours = form.total_hours.data or 0.0
        course.num_sessions = form.num_sessions.data

        CourseSchedule.query.filter_by(course_id=course.id).delete()

        for entry in form.schedules.entries:
            if entry.start_time.data and entry.end_time.data:
                sched = CourseSchedule(
                    course_id=course.id,
                    weekday=entry.weekday.data,
                    start_time=entry.start_time.data.strip(),
                    end_time=entry.end_time.data.strip(),
                )
                db.session.add(sched)
        db.session.commit()
        flash(f'Course "{course.name}" updated successfully.', 'success')
        return redirect(url_for('courses.detail', course_id=course.id))
    return render_template('courses/edit.html', form=form, course=course)


@courses_bp.route('/<int:course_id>/groups/create', methods=['GET', 'POST'])
@role_required('admin')
def create_group(course_id):
    course = Course.query.get_or_404(course_id)
    form = GroupForm()
    # Populate instructor choices
    instructors = Instructor.query.join(Instructor.user).all()
    form.instructor_id.choices = [(i.id, i.user.full_name) for i in instructors]

    if form.validate_on_submit():
        group = Group(
            course_id=course.id,
            instructor_id=form.instructor_id.data,
            name=form.name.data,
            schedule_day=form.schedule_day.data,
            schedule_time=form.schedule_time.data,
            max_capacity=form.max_capacity.data or 30,
        )
        db.session.add(group)
        db.session.commit()
        flash(f'Group "{group.name}" added to {course.name}.', 'success')
        return redirect(url_for('courses.detail', course_id=course.id))
    return render_template('courses/create_group.html', form=form, course=course)


@courses_bp.route('/<int:course_id>/enroll', methods=['GET', 'POST'])
@role_required('admin')
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    form = EnrollmentForm()

    # Populate choices
    students = Student.query.join(Student.user).all()
    form.student_id.choices = [(s.id, s.user.full_name) for s in students]
    groups = course.groups.filter_by(is_active=True).all()
    form.group_id.choices = [(g.id, f'{g.name} ({g.schedule_day} {g.schedule_time})') for g in groups]

    if form.validate_on_submit():
        # Check if already enrolled
        existing = Enrollment.query.filter_by(
            student_id=form.student_id.data,
            course_id=course.id
        ).first()
        if existing:
            flash('This student is already enrolled in this course.', 'warning')
            return redirect(url_for('courses.detail', course_id=course.id))

        # Check group capacity
        group = Group.query.get(form.group_id.data)
        if group.current_count >= group.max_capacity:
            flash('This group has reached its maximum capacity.', 'danger')
            return redirect(url_for('courses.enroll', course_id=course.id))

        enrollment = Enrollment(
            student_id=form.student_id.data,
            course_id=course.id,
            group_id=form.group_id.data,
        )
        db.session.add(enrollment)
        db.session.commit()
        flash('Student enrolled successfully.', 'success')
        return redirect(url_for('courses.detail', course_id=course.id))

    return render_template('courses/enroll.html', form=form, course=course)

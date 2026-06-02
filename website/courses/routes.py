from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user

from . import courses_bp
from .forms import CourseForm, GroupForm, EnrollmentForm
from ..extensions import db
from ..models import Course, Group, Enrollment, Instructor, Student
from ..utils import role_required


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
    if form.validate_on_submit():
        course = Course(
            name=form.name.data,
            description=form.description.data,
            level=form.level.data,
            duration_weeks=form.duration_weeks.data,
            reservation_fee=form.reservation_fee.data or 0.0,
            course_fee=form.course_fee.data or 0.0,
            certificate_fee=form.certificate_fee.data or 0.0,
        )
        db.session.add(course)
        db.session.commit()
        flash(f'Course "{course.name}" created successfully.', 'success')
        return redirect(url_for('courses.detail', course_id=course.id))
    return render_template('courses/create.html', form=form)


@courses_bp.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        form.populate_obj(course)
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

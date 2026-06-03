import os
import uuid

from flask import render_template, abort, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from . import students_bp
from .forms import (StudentEditForm, StudentPhotoForm, StudentProjectForm,
                    InstructorNoteForm, TrainerEvaluationForm,
                    AssignmentSubmissionForm, ParticipationScoreForm)
from ..models import (Student, StudentProject, ProjectMedia, InstructorNote,
                      TrainerEvaluation, Assignment, AssignmentSubmission,
                      Instructor, Course, Enrollment, Attendance)
from ..extensions import db
from ..utils import (role_required, compute_assignment_completion_rate,
                     compute_overall_attendance_rate, compute_participation_score,
                     compute_project_completion_rate)


@students_bp.route('/')
@role_required('admin')
def list_students():
    students = Student.query.join(Student.user).order_by(Student.id.desc()).all()
    return render_template('students/list.html', students=students)


@students_bp.route('/profile')
@login_required
def profile():
    if current_user.role != 'student' or not current_user.student:
        abort(403)
    student = current_user.student
    return render_template('students/profile.html', student=student)


@students_bp.route('/<int:student_id>')
@role_required('admin', 'instructor')
def detail(student_id):
    student = Student.query.get_or_404(student_id)

    # --- KPI computations ---
    kpis = {
        'assignment_completion': compute_assignment_completion_rate(student),
        'attendance_rate':       compute_overall_attendance_rate(student),
        'participation_score':   compute_participation_score(student),
        'project_completion':    compute_project_completion_rate(student),
    }

    # Trainer evaluation: find evaluations for this student's enrollments
    trainer_evals = TrainerEvaluation.query.filter_by(student_id=student.id).all()
    avg_trainer_score = None
    if trainer_evals:
        avg_trainer_score = round(sum(e.score for e in trainer_evals) / len(trainer_evals), 1)

    # Portfolio projects
    projects = student.projects.order_by(StudentProject.created_at.desc()).all()

    # Instructor notes (most recent first)
    notes = student.instructor_notes.order_by(InstructorNote.created_at.desc()).all()

    # Forms for actions on this page
    note_form = InstructorNoteForm()
    instructors = Instructor.query.join(Instructor.user).all()
    note_form.instructor_id.choices = [(i.id, i.user.full_name) for i in instructors]
    courses = Course.query.filter_by(is_active=True).all()
    note_form.course_id.choices = [(c.id, c.name) for c in courses]

    eval_form = TrainerEvaluationForm()
    enrollments = student.enrollments.filter_by(status='active').all()
    eval_form.enrollment_id.choices = [
        (e.id, f'{e.course.name} — {e.group.name}') for e in enrollments
    ]
    eval_form.instructor_id.choices = [(i.id, i.user.full_name) for i in instructors]

    # Assignments for the student's enrolled courses
    enrolled_course_ids = [e.course_id for e in student.enrollments.all()]
    assignments = Assignment.query.filter(
        Assignment.course_id.in_(enrolled_course_ids)
    ).order_by(Assignment.created_at.desc()).all()

    # Pre-fetch this student's submissions as a dict: assignment_id → submission
    submission_map = {
        sub.assignment_id: sub
        for sub in AssignmentSubmission.query.filter_by(student_id=student.id).all()
    }

    photo_form = StudentPhotoForm()

    return render_template(
        'students/detail.html',
        student=student,
        kpis=kpis,
        avg_trainer_score=avg_trainer_score,
        trainer_evals=trainer_evals,
        projects=projects,
        notes=notes,
        note_form=note_form,
        eval_form=eval_form,
        assignments=assignments,
        submission_map=submission_map,
        photo_form=photo_form,
    )


@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(student_id):
    student = Student.query.get_or_404(student_id)
    user    = student.user
    form    = StudentEditForm()

    if form.validate_on_submit():
        # --- Minor validation: guardian_phone mandatory if student is a minor ---
        from datetime import date as _date
        dob = form.date_of_birth.data
        is_minor = False
        if dob:
            today = _date.today()
            age = (today.year - dob.year
                   - ((today.month, today.day) < (dob.month, dob.day)))
            is_minor = age < 18
        if is_minor and not form.guardian_phone.data:
            form.guardian_phone.errors.append(
                'Parent/Guardian phone is mandatory for students under 18.'
            )
            return render_template('students/edit.html', form=form, student=student)

        # --- Email uniqueness check (skip if same user) ---
        from ..models import User
        existing = User.query.filter_by(email=form.email.data).first()
        if existing and existing.id != user.id:
            flash('This email address is already in use by another account.', 'danger')
            return render_template('students/edit.html', form=form, student=student)

        # --- Update User fields ---
        user.first_name = form.first_name.data
        user.last_name  = form.last_name.data
        user.phone      = form.phone.data
        user.email      = form.email.data

        # --- Update Student fields ---
        student.gender                  = form.gender.data or None
        student.date_of_birth           = form.date_of_birth.data
        student.nationality             = form.nationality.data
        student.address_line            = form.address_line.data
        student.city                    = form.city.data
        student.country                 = form.country.data
        student.guardian_phone          = form.guardian_phone.data
        student.emergency_contact_name  = form.emergency_contact_name.data
        student.emergency_contact_phone = form.emergency_contact_phone.data
        student.school_name             = form.school_name.data
        student.grade                   = form.grade.data
        student.notes                   = form.notes.data

        db.session.commit()
        flash(f'{user.full_name}\'s profile updated successfully.', 'success')
        return redirect(url_for('students.detail', student_id=student.id))

    # Populate form on GET
    if request.method == 'GET':
        form.first_name.data             = user.first_name
        form.last_name.data              = user.last_name
        form.phone.data                  = user.phone
        form.email.data                  = user.email
        form.gender.data                 = student.gender or ''
        form.date_of_birth.data          = student.date_of_birth
        form.nationality.data            = student.nationality
        form.address_line.data           = student.address_line
        form.city.data                   = student.city
        form.country.data                = student.country
        form.guardian_phone.data         = student.guardian_phone
        form.emergency_contact_name.data = student.emergency_contact_name
        form.emergency_contact_phone.data= student.emergency_contact_phone
        form.school_name.data            = student.school_name
        form.grade.data                  = student.grade
        form.notes.data                  = student.notes

    return render_template('students/edit.html', form=form, student=student)


@students_bp.route('/<int:student_id>/upload-photo', methods=['POST'])
@role_required('admin')
def upload_photo(student_id):
    student = Student.query.get_or_404(student_id)
    form    = StudentPhotoForm()
    if form.validate_on_submit():
        f = form.photo.data
        ext      = os.path.splitext(secure_filename(f.filename))[1].lower()
        filename = f'student_{student.id}_{uuid.uuid4().hex}{ext}'
        filepath = os.path.join(current_app.config['STUDENT_PHOTOS_DIR'], filename)
        f.save(filepath)
        student.photo_path = f'student_photos/{filename}'
        db.session.commit()
        flash('Profile photo updated.', 'success')
    else:
        flash('Invalid photo file.', 'danger')
    return redirect(url_for('students.detail', student_id=student.id))


@students_bp.route('/<int:student_id>/portfolio/create', methods=['GET', 'POST'])
@role_required('admin')
def create_project(student_id):
    student = Student.query.get_or_404(student_id)
    form    = StudentProjectForm()

    if form.validate_on_submit():
        # --- Validate at least one photo uploaded ---
        photo_files = request.files.getlist('photos')
        valid_photos = [f for f in photo_files if f and f.filename]
        if not valid_photos:
            flash('At least one project photo is required.', 'danger')
            return render_template('students/project_form.html',
                                   form=form, student=student, project=None)

        # --- Create project record ---
        project = StudentProject(
            student_id        = student.id,
            title             = form.title.data,
            description       = form.description.data,
            skills_used       = form.skills_used.data,
            project_link      = form.project_link.data or None,
            completion_status = form.completion_status.data,
            completion_score  = form.completion_score.data,
            instructor_remark = form.instructor_remark.data,
            created_by        = current_user.id,
        )
        db.session.add(project)
        db.session.flush()  # get project.id

        # --- Save media files ---
        def save_media(file_list, media_type):
            for f in file_list:
                if f and f.filename:
                    ext  = os.path.splitext(secure_filename(f.filename))[1].lower()
                    name = f'{media_type}_{project.id}_{uuid.uuid4().hex}{ext}'
                    path = os.path.join(current_app.config['PROJECT_MEDIA_DIR'], name)
                    f.save(path)
                    db.session.add(ProjectMedia(
                        project_id        = project.id,
                        media_type        = media_type,
                        file_path         = f'project_media/{name}',
                        original_filename = f.filename,
                    ))

        save_media(valid_photos, 'photo')
        save_media(request.files.getlist('videos'), 'video')
        save_media(request.files.getlist('files'),  'file')

        db.session.commit()
        flash(f'Project "{project.title}" added to portfolio.', 'success')
        return redirect(url_for('students.detail', student_id=student.id) + '#portfolio')

    return render_template('students/project_form.html',
                           form=form, student=student, project=None)


@students_bp.route('/portfolio/<int:project_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_project(project_id):
    project = StudentProject.query.get_or_404(project_id)
    student = project.student
    form    = StudentProjectForm(obj=project)

    if form.validate_on_submit():
        project.title             = form.title.data
        project.description       = form.description.data
        project.skills_used       = form.skills_used.data
        project.project_link      = form.project_link.data or None
        project.completion_status = form.completion_status.data
        project.completion_score  = form.completion_score.data
        project.instructor_remark = form.instructor_remark.data

        # New media files appended (not replacing existing ones)
        def save_media(file_list, media_type):
            for f in file_list:
                if f and f.filename:
                    ext  = os.path.splitext(secure_filename(f.filename))[1].lower()
                    name = f'{media_type}_{project.id}_{uuid.uuid4().hex}{ext}'
                    path = os.path.join(current_app.config['PROJECT_MEDIA_DIR'], name)
                    f.save(path)
                    db.session.add(ProjectMedia(
                        project_id        = project.id,
                        media_type        = media_type,
                        file_path         = f'project_media/{name}',
                        original_filename = f.filename,
                    ))

        save_media(request.files.getlist('photos'), 'photo')
        save_media(request.files.getlist('videos'), 'video')
        save_media(request.files.getlist('files'),  'file')

        db.session.commit()
        flash(f'Project "{project.title}" updated.', 'success')
        return redirect(url_for('students.detail', student_id=student.id) + '#portfolio')

    # On GET: pre-populate non-file fields (obj=project handles it)
    return render_template('students/project_form.html',
                           form=form, student=student, project=project)


@students_bp.route('/portfolio/<int:project_id>/delete', methods=['POST'])
@role_required('admin')
def delete_project(project_id):
    project = StudentProject.query.get_or_404(project_id)
    student_id = project.student_id
    # Physically delete media files from disk
    for media in project.media.all():
        filepath = os.path.join(current_app.config['STATIC_DIR'], media.file_path)
        if os.path.exists(filepath):
            os.remove(filepath)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted from portfolio.', 'success')
    return redirect(url_for('students.detail', student_id=student_id) + '#portfolio')


@students_bp.route('/portfolio/media/<int:media_id>/delete', methods=['POST'])
@role_required('admin')
def delete_project_media(media_id):
    media = ProjectMedia.query.get_or_404(media_id)
    student_id = media.project.student_id
    filepath = os.path.join(current_app.config['STATIC_DIR'], media.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(media)
    db.session.commit()
    flash('Media file removed.', 'info')
    return redirect(url_for('students.detail', student_id=student_id) + '#portfolio')


@students_bp.route('/<int:student_id>/notes/add', methods=['POST'])
@role_required('admin')
def add_instructor_note(student_id):
    student     = Student.query.get_or_404(student_id)
    instructors = Instructor.query.join(Instructor.user).all()
    courses     = Course.query.filter_by(is_active=True).all()
    form        = InstructorNoteForm()
    form.instructor_id.choices = [(i.id, i.user.full_name) for i in instructors]
    form.course_id.choices     = [(c.id, c.name) for c in courses]

    if form.validate_on_submit():
        note = InstructorNote(
            student_id    = student.id,
            instructor_id = form.instructor_id.data,
            course_id     = form.course_id.data,
            body          = form.body.data,
            created_by    = current_user.id,
        )
        db.session.add(note)
        db.session.commit()
        flash('Instructor note added.', 'success')
    else:
        flash('Failed to add note. Please check all fields.', 'danger')
    return redirect(url_for('students.detail', student_id=student.id) + '#notes')


@students_bp.route('/notes/<int:note_id>/delete', methods=['POST'])
@role_required('admin')
def delete_instructor_note(note_id):
    note = InstructorNote.query.get_or_404(note_id)
    student_id = note.student_id
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted.', 'info')
    return redirect(url_for('students.detail', student_id=student_id) + '#notes')


@students_bp.route('/<int:student_id>/evaluation', methods=['POST'])
@role_required('admin', 'instructor')
def record_trainer_evaluation(student_id):
    student     = Student.query.get_or_404(student_id)
    instructors = Instructor.query.join(Instructor.user).all()
    enrollments = student.enrollments.filter_by(status='active').all()
    form        = TrainerEvaluationForm()
    form.enrollment_id.choices = [
        (e.id, f'{e.course.name} — {e.group.name}') for e in enrollments
    ]
    form.instructor_id.choices = [(i.id, i.user.full_name) for i in instructors]

    if form.validate_on_submit():
        existing = TrainerEvaluation.query.filter_by(
            enrollment_id = form.enrollment_id.data,
            instructor_id = form.instructor_id.data,
        ).first()
        if existing:
            existing.score       = form.score.data
            existing.feedback    = form.feedback.data
            existing.evaluated_by= current_user.id
        else:
            ev = TrainerEvaluation(
                student_id    = student.id,
                enrollment_id = form.enrollment_id.data,
                instructor_id = form.instructor_id.data,
                score         = form.score.data,
                feedback      = form.feedback.data,
                evaluated_by  = current_user.id,
            )
            db.session.add(ev)
        db.session.commit()
        flash('Trainer evaluation saved.', 'success')
    else:
        flash('Failed to save evaluation. Check all fields.', 'danger')
    return redirect(url_for('students.detail', student_id=student.id) + '#kpis')


@students_bp.route('/<int:student_id>/assignments/<int:assignment_id>/submission',
                   methods=['POST'])
@role_required('admin')
def record_assignment_submission(student_id, assignment_id):
    student    = Student.query.get_or_404(student_id)
    assignment = Assignment.query.get_or_404(assignment_id)
    form       = AssignmentSubmissionForm()

    if form.validate_on_submit():
        existing = AssignmentSubmission.query.filter_by(
            assignment_id = assignment.id,
            student_id    = student.id,
        ).first()
        if existing:
            existing.status      = form.status.data
            existing.notes       = form.notes.data
            existing.recorded_by = current_user.id
        else:
            sub = AssignmentSubmission(
                assignment_id = assignment.id,
                student_id    = student.id,
                status        = form.status.data,
                notes         = form.notes.data,
                recorded_by   = current_user.id,
            )
            db.session.add(sub)
        db.session.commit()
        flash(f'Submission recorded for "{assignment.title}".', 'success')
    else:
        flash('Failed to record submission.', 'danger')
    return redirect(url_for('students.detail', student_id=student.id) + '#kpis')

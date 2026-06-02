from flask import render_template, abort
from flask_login import current_user, login_required

from . import students_bp
from ..models import Student
from ..utils import role_required


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
    return render_template('students/detail.html', student=student)

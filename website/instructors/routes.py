from flask import render_template, abort
from flask_login import current_user, login_required

from . import instructors_bp
from ..models import Instructor
from ..utils import role_required


@instructors_bp.route('/')
@role_required('admin')
def list_instructors():
    instructors = Instructor.query.join(Instructor.user).order_by(Instructor.id.desc()).all()
    return render_template('instructors/list.html', instructors=instructors)


@instructors_bp.route('/profile')
@login_required
def profile():
    if current_user.role != 'instructor' or not current_user.instructor:
        abort(403)
    instructor = current_user.instructor
    return render_template('instructors/profile.html', instructor=instructor)


@instructors_bp.route('/<int:instructor_id>')
@role_required('admin')
def detail(instructor_id):
    instructor = Instructor.query.get_or_404(instructor_id)
    return render_template('instructors/detail.html', instructor=instructor)

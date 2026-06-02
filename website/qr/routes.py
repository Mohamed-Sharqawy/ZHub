import os

import qrcode
from flask import render_template, redirect, url_for, flash, current_app

from . import qr_bp
from ..extensions import db
from ..models import Student
from ..utils import role_required


@qr_bp.route('/generate/<int:student_id>', methods=['POST'])
@role_required('admin')
def generate(student_id):
    student = Student.query.get_or_404(student_id)

    # Build the URL the QR code will encode
    scan_url = url_for('qr.scan', token=student.qr_token, _external=True)

    # Generate QR image
    qr_img = qrcode.make(scan_url)
    filename = f'qr_{student.qr_token}.png'
    filepath = os.path.join(current_app.config['QR_CODES_DIR'], filename)
    qr_img.save(filepath)

    # Save path to student record
    student.qr_image_path = f'qrcodes/{filename}'
    db.session.commit()

    flash(f'QR code generated for {student.user.full_name}.', 'success')
    return redirect(url_for('students.detail', student_id=student.id))


@qr_bp.route('/scan/<token>')
def scan(token):
    """Public route: scanning a QR code redirects to student profile info."""
    student = Student.query.filter_by(qr_token=token).first_or_404()
    return render_template('qr/scan_result.html', student=student)

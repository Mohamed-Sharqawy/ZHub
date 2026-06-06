import os
from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, send_file, current_app
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from . import certificates_bp
from ..extensions import db
from ..models import Certificate, Student, Course, Transaction
from ..utils import role_required


@certificates_bp.route('/')
@role_required('admin')
def list_certificates():
    certificates = Certificate.query.order_by(Certificate.issued_at.desc()).all()
    return render_template('certificates/list.html', certificates=certificates)


@certificates_bp.route('/generate', methods=['POST'])
@role_required('admin')
def generate():
    from flask import request
    student_id = request.form.get('student_id', type=int)
    course_id = request.form.get('course_id', type=int)

    student = Student.query.get_or_404(student_id)
    course = Course.query.get_or_404(course_id)

    # Check certificate fee has been paid
    cert_payment = Transaction.query.filter_by(
        student_id=student.id,
        course_id=course.id,
    ).first()

    if not cert_payment:
        flash('Certificate fee has not been paid. Cannot generate certificate.', 'danger')
        return redirect(url_for('students.detail', student_id=student.id))

    # Check if certificate already exists
    existing = Certificate.query.filter_by(
        student_id=student.id,
        course_id=course.id
    ).first()
    if existing:
        flash('Certificate already exists for this student and course.', 'warning')
        return redirect(url_for('certificates.list_certificates'))

    # Generate PDF
    filename = f'cert_{student.id}_{course.id}.pdf'
    filepath = os.path.join(current_app.config['CERTIFICATES_DIR'], filename)
    _generate_pdf(filepath, student, course)

    # Save certificate record
    cert = Certificate(
        student_id=student.id,
        course_id=course.id,
        file_path=f'certificates/{filename}',
    )
    db.session.add(cert)
    db.session.commit()

    flash(f'Certificate generated for {student.user.full_name}.', 'success')
    return redirect(url_for('certificates.list_certificates'))


@certificates_bp.route('/download/<int:cert_id>')
@role_required('admin', 'student')
def download(cert_id):
    from flask_login import current_user
    cert = Certificate.query.get_or_404(cert_id)

    # Students can only download their own
    if current_user.role == 'student':
        if not current_user.student or current_user.student.id != cert.student_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.home'))

    filepath = os.path.join(current_app.config['CERTIFICATES_DIR'], os.path.basename(cert.file_path))
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(cert.file_path))


def _generate_pdf(filepath, student, course):
    """Generate a clean A4 landscape PDF certificate."""
    c = canvas.Canvas(filepath, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Border
    c.setStrokeColorRGB(0.2, 0.4, 0.7)
    c.setLineWidth(4)
    c.rect(1.5 * cm, 1.5 * cm, width - 3 * cm, height - 3 * cm)

    # Inner border
    c.setStrokeColorRGB(0.6, 0.7, 0.9)
    c.setLineWidth(1.5)
    c.rect(2 * cm, 2 * cm, width - 4 * cm, height - 4 * cm)

    # Title
    c.setFont('Helvetica-Bold', 36)
    c.setFillColorRGB(0.2, 0.3, 0.6)
    c.drawCentredString(width / 2, height - 5 * cm, 'Certificate of Completion')

    # Subtitle
    c.setFont('Helvetica', 16)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(width / 2, height - 7 * cm, 'This is to certify that')

    # Student name
    c.setFont('Helvetica-Bold', 28)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawCentredString(width / 2, height - 9 * cm, student.user.full_name)

    # Course completion text
    c.setFont('Helvetica', 16)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(width / 2, height - 11 * cm, 'has successfully completed the course')

    # Course name
    c.setFont('Helvetica-Bold', 22)
    c.setFillColorRGB(0.2, 0.4, 0.7)
    c.drawCentredString(width / 2, height - 13 * cm, course.name)

    # Date
    c.setFont('Helvetica', 12)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    issue_date = datetime.now(timezone.utc).strftime('%B %d, %Y')
    c.drawCentredString(width / 2, height - 15.5 * cm, f'Date: {issue_date}')

    # Footer
    c.setFont('Helvetica-Oblique', 10)
    c.drawCentredString(width / 2, 2.5 * cm, 'ZHub Course Center')

    c.save()

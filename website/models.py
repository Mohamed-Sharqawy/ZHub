import uuid
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # admin / instructor / student
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # One-to-one relationships
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    instructor = db.relationship('Instructor', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


# ---------------------------------------------------------------------------
# Student
# ---------------------------------------------------------------------------
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    qr_token = db.Column(db.String(64), unique=True, default=lambda: uuid.uuid4().hex)
    qr_image_path = db.Column(db.String(256))
    date_of_birth = db.Column(db.Date)
    guardian_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)

    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    course_ratings = db.relationship('CourseRating', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    instructor_ratings = db.relationship('InstructorRating', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.user.full_name}>'


# ---------------------------------------------------------------------------
# Instructor
# ---------------------------------------------------------------------------
class Instructor(db.Model):
    __tablename__ = 'instructors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialization = db.Column(db.String(200))
    bio = db.Column(db.Text)

    groups = db.relationship('Group', backref='instructor', lazy='dynamic')
    ratings = db.relationship('InstructorRating', backref='instructor', lazy='dynamic')

    def __repr__(self):
        return f'<Instructor {self.user.full_name}>'


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------
class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.String(50))  # beginner / intermediate / advanced
    duration_weeks = db.Column(db.Integer)
    reservation_fee = db.Column(db.Float, default=0.0)
    course_fee = db.Column(db.Float, default=0.0)
    certificate_fee = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    groups = db.relationship('Group', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    ratings = db.relationship('CourseRating', backref='course', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.name}>'


# ---------------------------------------------------------------------------
# Group (section of a course)
# ---------------------------------------------------------------------------
class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    schedule_day = db.Column(db.String(20))   # e.g. "Saturday"
    schedule_time = db.Column(db.String(20))  # e.g. "10:00 AM"
    max_capacity = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)

    enrollments = db.relationship('Enrollment', backref='group', lazy='dynamic')
    attendance_records = db.relationship('Attendance', backref='group', lazy='dynamic')

    @property
    def current_count(self):
        return self.enrollments.filter_by(status='active').count()

    def __repr__(self):
        return f'<Group {self.name} - {self.course.name}>'


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------
class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='active')  # active / completed / dropped

    attendance_records = db.relationship('Attendance', backref='enrollment', lazy='dynamic', cascade='all, delete-orphan')
    performance = db.relationship('StudentPerformance', backref='enrollment', uselist=False, cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_course'),
    )

    def __repr__(self):
        return f'<Enrollment student={self.student_id} course={self.course_id}>'


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='absent')  # present / absent
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    __table_args__ = (
        db.UniqueConstraint('enrollment_id', 'date', name='uq_enrollment_date'),
    )

    def __repr__(self):
        return f'<Attendance enrollment={self.enrollment_id} {self.date} {self.status}>'


# ---------------------------------------------------------------------------
# Student Performance
# ---------------------------------------------------------------------------
class StudentPerformance(db.Model):
    __tablename__ = 'student_performance'

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), unique=True, nullable=False)
    score = db.Column(db.Float)
    feedback = db.Column(db.Text)
    evaluated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    evaluated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Performance enrollment={self.enrollment_id} score={self.score}>'


# ---------------------------------------------------------------------------
# Course Rating
# ---------------------------------------------------------------------------
class CourseRating(db.Model):
    __tablename__ = 'course_ratings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_course_rating'),
    )

    def __repr__(self):
        return f'<CourseRating student={self.student_id} course={self.course_id} rating={self.rating}>'


# ---------------------------------------------------------------------------
# Instructor Rating
# ---------------------------------------------------------------------------
class InstructorRating(db.Model):
    __tablename__ = 'instructor_ratings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('student_id', 'instructor_id', name='uq_student_instructor_rating'),
    )

    def __repr__(self):
        return f'<InstructorRating student={self.student_id} instructor={self.instructor_id} rating={self.rating}>'


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------
class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # reservation / course / certificate
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    received_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)

    course = db.relationship('Course', backref='payments')

    def __repr__(self):
        return f'<Payment student={self.student_id} type={self.payment_type} amount={self.amount}>'


# ---------------------------------------------------------------------------
# Certificate
# ---------------------------------------------------------------------------
class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    course = db.relationship('Course', backref='certificates')

    def __repr__(self):
        return f'<Certificate student={self.student_id} course={self.course_id}>'

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
    email = db.Column(db.String(150), unique=True, nullable=True, index=True)
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

    # Extended personal info
    photo_path              = db.Column(db.String(256), nullable=True)
    gender                  = db.Column(db.String(20), nullable=True)    # 'male', 'female', 'prefer_not_to_say'
    nationality             = db.Column(db.String(100), nullable=True)
    address_line            = db.Column(db.Text, nullable=True)
    city                    = db.Column(db.String(100), nullable=True)
    country                 = db.Column(db.String(100), nullable=True)
    emergency_contact_name  = db.Column(db.String(150), nullable=True)
    emergency_contact_phone = db.Column(db.String(30), nullable=True)
    school_name             = db.Column(db.String(200), nullable=True)
    grade                   = db.Column(db.String(50), nullable=True)

    @property
    def is_minor(self):
        """Returns True if the student is under 18 years old based on date_of_birth."""
        if not self.date_of_birth:
            return False
        from datetime import date
        today = date.today()
        age = (today.year - self.date_of_birth.year
               - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)))
        return age < 18

    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    course_ratings = db.relationship('CourseRating', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    instructor_ratings = db.relationship('InstructorRating', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    projects         = db.relationship('StudentProject', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    instructor_notes = db.relationship('InstructorNote', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    trainer_evals    = db.relationship('TrainerEvaluation', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    submissions      = db.relationship('AssignmentSubmission', backref='student', lazy='dynamic', cascade='all, delete-orphan')

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
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    total_hours = db.Column(db.Float, nullable=True)
    num_sessions = db.Column(db.Integer, nullable=True)

    groups = db.relationship('Group', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    ratings = db.relationship('CourseRating', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    schedules = db.relationship('CourseSchedule', backref='course', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.name}>'


# ---------------------------------------------------------------------------
# Course Schedule
# ---------------------------------------------------------------------------
class CourseSchedule(db.Model):
    __tablename__ = 'course_schedules'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    weekday = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)

    @property
    def duration_hours(self):
        from datetime import datetime
        start = datetime.strptime(self.start_time, '%H:%M').time()
        end = datetime.strptime(self.end_time, '%H:%M').time()
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        return (end_minutes - start_minutes) / 60.0

    def __repr__(self):
        return f'<CourseSchedule course={self.course_id} {self.weekday} {self.start_time}-{self.end_time}>'


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
    total_fee = db.Column(db.Float, default=0.0)
    total_paid = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='Unpaid')  # Unpaid / Partially Paid / Fully Paid

    @property
    def remaining_balance(self):
        return (self.total_fee or 0.0) - (self.total_paid or 0.0)

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
    participation_score = db.Column(db.Float, nullable=True)
    # Float 0.0–10.0, null means not recorded for this session

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
# Transaction
# ---------------------------------------------------------------------------
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)

    # ── Classification ──────────────────────────────────────────────────────
    transaction_kind = db.Column(db.String(10), nullable=False)
    # Allowed values: 'income' | 'expense'

    # ── Income-only fields (null when transaction_kind == 'expense') ────────
    student_id   = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    course_id    = db.Column(db.Integer, db.ForeignKey('courses.id'),  nullable=True)
    payment_type = db.Column(db.String(20), nullable=True)
    # Allowed values: 'reservation' | 'course' | 'certificate'
    total_amount = db.Column(db.Float, nullable=True)
    # The full fee expected for this payment category (e.g. 250 EGP)
    paid_amount  = db.Column(db.Float, nullable=True)
    # The actual amount received in this single transaction (e.g. 50 EGP)

    # ── Expense-only fields (null when transaction_kind == 'income') ────────
    expense_category    = db.Column(db.String(50), nullable=True)
    # Allowed values: 'electricity'|'water'|'gas'|'rent'|'maintenance'|'other'
    expense_description = db.Column(db.String(500), nullable=True)
    # Free-text required only when expense_category == 'other'

    # ── Common fields ────────────────────────────────────────────────────────
    amount      = db.Column(db.Float, nullable=False)
    # For income:  equals paid_amount (money received this transaction)
    # For expense: the amount paid out
    date        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes       = db.Column(db.Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    course = db.relationship('Course', backref=db.backref('course_transactions', lazy='dynamic'))

    @property
    def remaining_amount(self):
        """For income transactions: how much the student still owes on this payment."""
        if self.transaction_kind == 'income' and self.total_amount is not None:
            return round(max(0.0, self.total_amount - (self.paid_amount or 0.0)), 2)
        return 0.0

    @property
    def is_fully_paid(self):
        """True if an income transaction has no remaining balance."""
        return self.transaction_kind == 'income' and self.remaining_amount == 0.0

    def __repr__(self):
        return f'<Transaction {self.transaction_kind} amount={self.amount}>'


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


# ---------------------------------------------------------------------------
# StudentProject (Portfolio)
# ---------------------------------------------------------------------------
class StudentProject(db.Model):
    __tablename__ = 'student_projects'

    id                = db.Column(db.Integer, primary_key=True)
    student_id        = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    title             = db.Column(db.String(200), nullable=False)
    description       = db.Column(db.Text, nullable=True)
    skills_used       = db.Column(db.Text, nullable=False)
    # Comma-separated skill names, e.g. "Python,Flask,HTML,CSS"
    project_link      = db.Column(db.String(500), nullable=True)
    # Optional URL (Google Drive link, GitHub, etc.)
    completion_status = db.Column(db.String(30), nullable=False, default='not_evaluated')
    # Values: 'completed', 'partial', 'not_completed', 'not_evaluated'
    completion_score  = db.Column(db.Float, nullable=True)
    # 0.0–100.0, set by instructor/admin; null means not yet scored
    instructor_remark = db.Column(db.Text, nullable=True)
    # Short instructor remark specific to this project
    created_by        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    media = db.relationship('ProjectMedia', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def skills_list(self):
        """Return skills_used as a Python list, stripping whitespace."""
        if not self.skills_used:
            return []
        return [s.strip() for s in self.skills_used.split(',') if s.strip()]

    @property
    def photos(self):
        return self.media.filter_by(media_type='photo').all()

    @property
    def videos(self):
        return self.media.filter_by(media_type='video').all()

    @property
    def files(self):
        return self.media.filter_by(media_type='file').all()

    def __repr__(self):
        return f'<StudentProject {self.title} student={self.student_id}>'


# ---------------------------------------------------------------------------
# ProjectMedia (Photos / Videos / Files for a StudentProject)
# ---------------------------------------------------------------------------
class ProjectMedia(db.Model):
    __tablename__ = 'project_media'

    id                = db.Column(db.Integer, primary_key=True)
    project_id        = db.Column(db.Integer, db.ForeignKey('student_projects.id'), nullable=False, index=True)
    media_type        = db.Column(db.String(10), nullable=False)
    # Values: 'photo', 'video', 'file'
    file_path         = db.Column(db.String(256), nullable=False)
    # Path relative to STATIC_DIR, e.g. 'project_media/photo_123_abc.jpg'
    original_filename = db.Column(db.String(256), nullable=True)
    uploaded_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ProjectMedia {self.media_type} project={self.project_id}>'


# ---------------------------------------------------------------------------
# InstructorNote (Structured notes per instructor per course per student)
# ---------------------------------------------------------------------------
class InstructorNote(db.Model):
    __tablename__ = 'instructor_notes'

    id            = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'), nullable=False)
    course_id     = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    body          = db.Column(db.Text, nullable=False)
    created_by    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # The admin user who entered this note on behalf of the instructor
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    instructor = db.relationship('Instructor', backref='notes_given', foreign_keys=[instructor_id])
    course     = db.relationship('Course', backref='instructor_notes')

    def __repr__(self):
        return f'<InstructorNote student={self.student_id} instructor={self.instructor_id} course={self.course_id}>'


# ---------------------------------------------------------------------------
# Assignment (Task assigned to a course; students are expected to deliver)
# ---------------------------------------------------------------------------
class Assignment(db.Model):
    __tablename__ = 'assignments'

    id          = db.Column(db.Integer, primary_key=True)
    course_id   = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date    = db.Column(db.Date, nullable=True)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    course      = db.relationship('Course', backref='assignments')
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Assignment {self.title} course={self.course_id}>'


# ---------------------------------------------------------------------------
# AssignmentSubmission (Per-student delivery record for an Assignment)
# ---------------------------------------------------------------------------
class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'

    id            = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False, index=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    status        = db.Column(db.String(20), nullable=False, default='not_delivered')
    # Values: 'delivered', 'partial', 'not_delivered'
    notes         = db.Column(db.Text, nullable=True)
    recorded_by   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recorded_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('assignment_id', 'student_id', name='uq_assignment_student'),
    )

    def __repr__(self):
        return f'<AssignmentSubmission assignment={self.assignment_id} student={self.student_id} {self.status}>'


# ---------------------------------------------------------------------------
# TrainerEvaluation (Overall score given by instructor for a student in a course)
# ---------------------------------------------------------------------------
class TrainerEvaluation(db.Model):
    __tablename__ = 'trainer_evaluations'

    id            = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'), nullable=True)
    score         = db.Column(db.Float, nullable=False)
    # 0.0–100.0 scale
    feedback      = db.Column(db.Text, nullable=True)
    evaluated_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                              onupdate=lambda: datetime.now(timezone.utc))

    enrollment  = db.relationship('Enrollment', backref='trainer_evals')
    instructor  = db.relationship('Instructor', backref='evaluations_given')

    __table_args__ = (
        db.UniqueConstraint('enrollment_id', 'instructor_id', name='uq_eval_enrollment_instructor'),
    )

    def __repr__(self):
        return f'<TrainerEvaluation student={self.student_id} enrollment={self.enrollment_id} score={self.score}>'

import os
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired, MultipleFileField
from wtforms import (StringField, TextAreaField, SelectField, DateField,
                     FloatField, SubmitField, URLField)
from wtforms.validators import DataRequired, Optional, Email, Length, NumberRange


ALLOWED_PHOTO_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv', 'webm']
ALLOWED_FILE_EXTENSIONS  = ['pdf', 'doc', 'docx', 'zip', 'pptx', 'xlsx', 'txt']


class StudentEditForm(FlaskForm):
    """Form for admin to edit a student's extended personal information."""
    # Fields from User model (patched through to user)
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name  = StringField('Last Name',  validators=[DataRequired(), Length(max=100)])
    phone      = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    email      = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=150)])

    # Fields directly on Student model
    gender       = SelectField('Gender', choices=[
        ('', '— Select —'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ], validators=[Optional()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    nationality   = StringField('Nationality', validators=[Optional(), Length(max=100)])
    address_line  = TextAreaField('Address', validators=[Optional()])
    city          = StringField('City', validators=[Optional(), Length(max=100)])
    country       = StringField('Country', validators=[Optional(), Length(max=100)])
    guardian_phone = StringField('Parent / Guardian Phone',
                                 validators=[Optional(), Length(max=30)])
    # NOTE: guardian_phone becomes mandatory server-side if student is a minor.
    emergency_contact_name  = StringField('Emergency Contact Name',
                                          validators=[Optional(), Length(max=150)])
    emergency_contact_phone = StringField('Emergency Contact Phone',
                                          validators=[Optional(), Length(max=30)])
    school_name = StringField('School Name', validators=[Optional(), Length(max=200)])
    grade       = StringField('Grade / Year', validators=[Optional(), Length(max=50)])
    notes       = TextAreaField('Internal Admin Notes', validators=[Optional()])
    submit      = SubmitField('Save Changes')


class StudentPhotoForm(FlaskForm):
    """Form for uploading a student profile photo."""
    photo  = FileField('Profile Photo',
                       validators=[
                           FileRequired(message='Please select a photo.'),
                           FileAllowed(ALLOWED_PHOTO_EXTENSIONS,
                                       message='Only image files are allowed (jpg, jpeg, png, gif, webp).')
                       ])
    submit = SubmitField('Upload Photo')


class StudentProjectForm(FlaskForm):
    """Form for creating or editing a portfolio project."""
    title             = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    description       = TextAreaField('Project Description', validators=[Optional()])
    skills_used       = StringField('Skills Used',
                                    validators=[DataRequired(), Length(max=500)],
                                    description='Comma-separated, e.g. Python, Flask, HTML, CSS')
    project_link      = StringField('Project / Drive Link', validators=[Optional(), Length(max=500)])
    completion_status = SelectField('Completion Status', choices=[
        ('not_evaluated', 'Not Evaluated'),
        ('completed',     'Completed'),
        ('partial',       'Partially Completed'),
        ('not_completed', 'Not Completed'),
    ], validators=[DataRequired()])
    completion_score  = FloatField('Completion Score (0–100)',
                                   validators=[Optional(), NumberRange(min=0, max=100)])
    instructor_remark = TextAreaField('Instructor Remark', validators=[Optional()])

    # File uploads — handled via request.files in the route, not WTForms validators,
    # because WTForms MultipleFileField validation for "at least one required" is
    # enforced manually server-side.
    photos = MultipleFileField('Project Photos (required, at least 1)',
                               validators=[
                                   FileAllowed(ALLOWED_PHOTO_EXTENSIONS,
                                               'Only image files allowed.')
                               ])
    videos = MultipleFileField('Videos (optional)',
                               validators=[
                                   FileAllowed(ALLOWED_VIDEO_EXTENSIONS,
                                               'Only video files allowed.')
                               ])
    files  = MultipleFileField('Files (optional)',
                               validators=[
                                   FileAllowed(ALLOWED_FILE_EXTENSIONS,
                                               'Only document/archive files allowed.')
                               ])
    submit = SubmitField('Save Project')


class InstructorNoteForm(FlaskForm):
    """Form for admin to add a structured instructor note about a student."""
    instructor_id = SelectField('Instructor', coerce=int, validators=[DataRequired()])
    course_id     = SelectField('Course',     coerce=int, validators=[DataRequired()])
    body          = TextAreaField('Note Body', validators=[DataRequired(), Length(min=5)])
    submit        = SubmitField('Add Note')


class TrainerEvaluationForm(FlaskForm):
    """Form for admin/instructor to record or update a trainer evaluation score."""
    enrollment_id = SelectField('Enrollment (Course – Group)', coerce=int,
                                validators=[DataRequired()])
    instructor_id = SelectField('Evaluating Instructor', coerce=int,
                                validators=[DataRequired()])
    score         = FloatField('Score (0–100)',
                               validators=[DataRequired(), NumberRange(min=0, max=100)])
    feedback      = TextAreaField('Feedback / Comments', validators=[Optional()])
    submit        = SubmitField('Save Evaluation')


class AssignmentForm(FlaskForm):
    """Form for admin to create an assignment for a course."""
    course_id   = SelectField('Course', coerce=int, validators=[DataRequired()])
    title       = StringField('Assignment Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description / Instructions', validators=[Optional()])
    due_date    = DateField('Due Date', validators=[Optional()])
    submit      = SubmitField('Create Assignment')


class AssignmentSubmissionForm(FlaskForm):
    """Form for admin to record a student's assignment submission status."""
    status = SelectField('Submission Status', choices=[
        ('not_delivered', 'Not Delivered'),
        ('delivered',     'Delivered'),
        ('partial',       'Partially Delivered'),
    ], validators=[DataRequired()])
    notes  = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save')


class ParticipationScoreForm(FlaskForm):
    """Form for admin/instructor to set participation score on an attendance record."""
    score  = FloatField('Participation Score (0.0–10.0)',
                        validators=[DataRequired(), NumberRange(min=0.0, max=10.0)])
    submit = SubmitField('Save')

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    level = SelectField('Level', choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], validators=[DataRequired()])
    duration_weeks = IntegerField('Duration (weeks)', validators=[Optional(), NumberRange(min=1)])
    reservation_fee = FloatField('Reservation Fee', validators=[Optional()], default=0.0)
    course_fee = FloatField('Course Fee', validators=[Optional()], default=0.0)
    certificate_fee = FloatField('Certificate Fee', validators=[Optional()], default=0.0)
    submit = SubmitField('Save Course')


class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    instructor_id = SelectField('Instructor', coerce=int, validators=[DataRequired()])
    schedule_day = SelectField('Day', choices=[
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
    ], validators=[DataRequired()])
    schedule_time = StringField('Time (e.g. 10:00 AM)', validators=[DataRequired()])
    max_capacity = IntegerField('Max Capacity', validators=[Optional(), NumberRange(min=1)], default=30)
    submit = SubmitField('Save Group')


class EnrollmentForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    group_id = SelectField('Group', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Enroll Student')

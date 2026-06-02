from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, Optional, EqualTo, Length


class UserCreateForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    ], validators=[DataRequired()])

    # Student-specific (shown conditionally)
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    guardian_phone = StringField('Guardian Phone', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])

    # Instructor-specific (shown conditionally)
    specialization = StringField('Specialization', validators=[Optional()])
    bio = TextAreaField('Bio', validators=[Optional()])

    submit = SubmitField('Create User')

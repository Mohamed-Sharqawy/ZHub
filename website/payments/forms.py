from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class PaymentForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    payment_type = SelectField('Payment Type', choices=[
        ('reservation', 'Reservation Fee'),
        ('course', 'Course Fee'),
        ('certificate', 'Certificate Fee'),
    ], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Record Payment')

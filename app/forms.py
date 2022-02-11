from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, widgets, SelectMultipleField
from wtforms.fields.core import DateField, SelectField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class CreatePolicyForm(FlaskForm):
    FrameNumber = StringField('Enter FrameNumber', validators=[DataRequired()])
    ReplacementValue = FloatField('Enter Replacement Value', default=0, validators=[DataRequired(), Length(max=5)])
    submit = SubmitField('Get Offer')

class CreateClaim(FlaskForm):
    Description = StringField('Enter Description (max. 200 words)', validators=[DataRequired()])
    Dateofloss = DateField('Enter Incident Date', default=0, validators=[DataRequired()])
    lossineuro = StringField('Enter loss in €', default = 0,validators=[DataRequired()])
    submit = SubmitField('Submit Claim')
    cancel = SubmitField('Cancel Claim')
    
class Offer(FlaskForm):
    FrameNumber = StringField('Enter FrameNumber', validators=[DataRequired()])
    ReplacementValue = FloatField('Enter Replacement Value', default=0, validators=[DataRequired()])
    submit = SubmitField('Get Offer')
    accept = SubmitField("Accept")
    decline = SubmitField("Decline")    
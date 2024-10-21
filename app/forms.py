from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email
from app.models import Role

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class EditProfileForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EditUserForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])
    role = SelectField('Role',choices = [data.value for data in Role], validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])

class EditStopForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])

class EditLineForm(FlaskForm):
    num = StringField('Line Number', validators=[DataRequired()])
    duration = StringField('Time duration between stops (min)', validators=[DataRequired()])
    stops = StringField('Stops', validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])

class EditVehicleForm(FlaskForm):
    spz = StringField('SPZ', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()])
    brand = StringField('Brand', validators=[DataRequired()])
    condition = StringField('Condition', validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])

class EditConnectionForm(FlaskForm):
    departure = StringField('Departure time:', validators=[DataRequired()])
    direction = SelectField('Direction:', choices=["up","down"], validators=[DataRequired()])
    only_working_days = BooleanField('Only working days:')
    vehicle_username = StringField('Vehicle name:', validators=[DataRequired()])
    driver_name = StringField('Driver name:', validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])

class EditRequestForm(FlaskForm):
    description = StringField('Description:', validators=[DataRequired()])
    deadline = DateField('Deadline:', validators=[DataRequired()])
    is_done = BooleanField('Is done:')
    vehicle_username = StringField('Vehicle name:', validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])

class EditMaintenaceRecordForm(FlaskForm):
    status = StringField('Status:', validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])

class EditDefectForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    vehicle = StringField('Vehicle name:', validators=[DataRequired()])
    submit = SubmitField('Submit', validators=[DataRequired()])

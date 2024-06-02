"""Forms for fitfeasters app."""

from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length, NumberRange, Email, Optional, EqualTo
from flask_wtf import FlaskForm


class LoginForm(FlaskForm):
    """Login form."""
    
    class Meta:
        csrf = False

    username = StringField(
        "Username",
        validators=[InputRequired()],
    )
    password = PasswordField(
        "Password",
        validators=[InputRequired(), Length(min=6)],
    )


class SignUpForm(FlaskForm):
    """User registration form."""

    class Meta:
        csrf = False
        
    username = StringField(
        "Username",
        validators=[InputRequired(), Length(min=6, max=20)],
    )
    password = PasswordField(
        "Password",
        validators=[InputRequired(), Length(min=6, max=250)],
    )
    email = StringField(
        "Email",
        validators=[InputRequired(), Email(), Length(min= 5, max=25)],
    )
    first_name = StringField(
        "First Name",
        validators=[InputRequired(), Length(max=30)],
    )
    last_name = StringField(
        "Last Name",
        validators=[InputRequired(), Length(max=30)],
    )
    image_url= StringField(
        '(Optional) Image URL'
    )
    
class UserEditForm(FlaskForm):
    """form to edit user"""

    username = StringField('Username', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('New Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('password')])
    image_url = StringField('(Optional) Image URL')


class DeleteForm(FlaskForm):
    """Delete form -- this form is intentionally blank."""


class SearchForm(FlaskForm):
    """Search for Recipes using API"""
    
    title = StringField(
        "Name",
        validators=[InputRequired(), Length(max=45)],
    )
    intolerances = StringField(
        "Any Food Intolerances?",
        validators=[Optional()],
    )
    includeIngredients = StringField(
        "What ingredients should be included?",
        validators=[Optional()],
    )

    
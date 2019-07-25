from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo
from models import User


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=3, max=8)])
    repeat = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        if User.query.filter_by(username=self.username.data).first():
            errors = list(self.username.errors)
            errors.append("Username is exists!")
            self.username.errors = errors
            return False

        user = User(self.username.data)
        user.set_password(self.password.data)
        user.save()
        return True


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        user = self.get_user()

        if not user:
            self.username.errors.append('Unknown username')
            return False

        # we're comparing the plaintext pw with the the hash from the db
        if not user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False

        if not user.is_active:
            self.username.errors.append('User not activated')
            return False

        return True

    def get_user(self):
        return User.query.filter_by(username=self.username.data).first()


class ChatForm(FlaskForm):
    message = TextAreaField('Input your message', validators=[DataRequired()])
    send = SubmitField('Send')
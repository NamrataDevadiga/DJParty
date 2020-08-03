from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User,Song

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    user_type = RadioField('User Type', choices = [('User','User'),('Dj','Dj')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class AddSongForm(FlaskForm):
    song_name = StringField('Song Name', validators=[DataRequired()])
    song_artist = StringField('Song Artist', validators=[DataRequired()])
    song_genre = StringField('Song Genre', validators=[DataRequired()])
    submit = SubmitField('Add Song')

    def validate_song_name(self, song_name):
        song = Song.query.filter_by(song_name=song_name.data).first()
        if song is not None:
            raise ValidationError('Song already exists in the database')

class SearchSongForm(FlaskForm):
    song_name = StringField('Search by Song Name, Song Artist or Song Genre')
    submit = SubmitField('SEARCH')

class SearchSongForm2(FlaskForm):
    song_name = StringField('Search by Song Name')
    submit = SubmitField('Add')    

class CreatePlaylistForm(FlaskForm):
    playlist_name = StringField('Playlist Name', validators=[DataRequired()])
    submit = SubmitField('Create Playlist') 

class CreatePartyForm(FlaskForm):
    party_name = StringField('Party Name', validators=[DataRequired()])
    submit = SubmitField('Create Party') 
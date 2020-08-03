from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login

requests = db.Table('requests',
    db.Column('id',db.Integer,db.ForeignKey('user.id')),
    db.Column('song_id',db.Integer,db.ForeignKey('song.song_id'))
    )

adds = db.Table('adds',
    db.Column('id',db.Integer,db.ForeignKey('user.id')),
    db.Column('playlist_id',db.Integer,db.ForeignKey('playlist.playlist_id'))
    )

contains = db.Table('contains',
    db.Column('song_id',db.Integer,db.ForeignKey('song.song_id')),
    db.Column('playlist_id',db.Integer,db.ForeignKey('playlist.playlist_id'))
    )

creates = db.Table('creates',
    db.Column('id',db.Integer,db.ForeignKey('user.id')),
    db.Column('party_id',db.Integer,db.ForeignKey('party.party_id'))
    )

plays = db.Table('plays',
    db.Column('playlist_id',db.Integer,db.ForeignKey('playlist.playlist_id')),
    db.Column('party_id',db.Integer,db.ForeignKey('party.party_id'))
    )

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(64))
    attempts = db.Column(db.Integer)
    accepted = db.Column(db.Integer)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}, User Type {}>'.format(self.username, self.user_type)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Song(db.Model):
    song_id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(64), index=True, unique=True)
    song_artist = db.Column(db.String(64), index=True)
    song_genre = db.Column(db.String(64), index=True)
    song_played = db.Column(db.Integer)
    score = db.Column(db.Integer)
    requested_by = db.relationship('User', secondary=requests, backref=db.backref('song_request'))

    def __repr__(self):
        return '<Song {}, Score {}, Played {}, Song Id {}, Song Artist {}, Song Genre {}>'.format(self.song_name, self.score, self.song_played, self.song_id, self.song_artist, self.song_genre)

    def as_dict(self):
    	return {'song_name':self.song_name}

    def as_dict_genre(self):
    	return {'song_name':self.song_genre}

    def as_dict_artist(self):
    	return {'song_name':self.song_artist}

class Playlist(db.Model):
    playlist_id = db.Column(db.Integer, primary_key=True)
    playlist_name = db.Column(db.String(140))
    added_by = db.relationship('User', secondary=adds, backref=db.backref('add_by'))
    contains_the = db.relationship('Song', secondary=contains, backref=db.backref('containing'))

    def __repr__(self):
        return '<Playlist {}>'.format(self.playlist_name)

class Party(db.Model):
	party_id = db.Column(db.Integer, primary_key=True)
	party_name = db.Column(db.String(140))
	party_on = db.Column(db.Integer)
	created_by = db.relationship('User', secondary=creates, backref=db.backref('create_by'))
	plays_the = db.relationship('Playlist', secondary=plays, backref=db.backref('play_the'))

	def __repr__(self):
		return '<Party {}, Party On {}, Party Id {}>'.format(self.party_name,self.party_on,self.party_id)

class Report(db.Model):
	report_id = db.Column(db.Integer, primary_key=True)
	party_id = db.Column(db.Integer)
	song_id = db.Column(db.Integer)
	requests = db.Column(db.Integer)
	accepted = db.Column(db.Integer)

	def __repr__(self):
		return '<Party {}, Song {}, Requests {}, Accepted {}>'.format(self.party_id,self.song_id,self.requests,self.accepted)

		
from flask import render_template, flash, redirect, url_for, jsonify
from app import app
from app.forms import LoginForm,RegistrationForm, AddSongForm, SearchSongForm, CreatePlaylistForm, CreatePartyForm, SearchSongForm2
from flask_login import current_user, login_user, logout_user, login_required
from app.models import *

flag = 0
if flag==0:
    db.create_all()

def recommend_songs(party_id):
    suggestion_list = []
    sql = 'SELECT * FROM plays where party_id='+party_id+';'
    a = db.engine.execute(sql)
    for i in a:
        playlist_id = i[0]
    playlist_songs = get_playlist_songs(playlist_id)
    genre_dict = dict()
    report = Report.query.filter_by(party_id=party_id).all()
    for r in report:
        song_id = r.song_id
        song = Song.query.filter_by(song_id=song_id).first()
        if song.song_genre in genre_dict:
            genre_dict[song.song_genre]+=1
        else:
            genre_dict[song.song_genre]=1
    sorted_dict = [(k, genre_dict[k]) for k in sorted(genre_dict, key=genre_dict.get, reverse=True)]
    for key,_ in sorted_dict:
        genre_songs = Song.query.filter_by(song_genre=key).all()
        for s in genre_songs:
            if s not in playlist_songs:
                suggestion_list.append(s)
                if len(suggestion_list)>=3:
                    return suggestion_list
    return suggestion_list


def clean_song_name(song_name):
    song_name = song_name.lower()
    song_name = " ".join(song_name.split())
    song_name = song_name.title()
    return song_name

def get_requested_songs(id):
    user = User.query.filter_by(id=id).first()
    songs = Song.query.join(requests).join(User).filter(requests.c.id == user.id).all()
    return songs

def get_top_requests(party_id):
    final_songs = []
    report = Report.query.filter_by(party_id=party_id).filter_by(accepted=0).all()
    for r in report:
        song_id = r.song_id
        song = Song.query.filter_by(song_id=song_id).first()
        if song.score%2 == 0:
            song.score = song.score/2
        final_songs.append((song,song.score))
    final_songs.sort(key = lambda x:x[1], reverse = True)
    final_songs = [x[0] for x in final_songs]
    return final_songs

def get_dj_accepts(party_id):
    songs = []
    report = Report.query.filter_by(party_id=party_id).filter_by(accepted=1).all()
    for r in report:
        song_id = r.song_id
        song = Song.query.filter_by(song_id=song_id).first()
        songs.append(song)
    return songs

def report_requests(party_id):
    reqs = dict()
    party = Party.query.filter_by(party_id=party_id).first()
    playlist = Playlist.query.join(plays).join(Party).filter(plays.c.party_id == party.party_id).first()
    playlist_songs = Song.query.join(contains).join(Playlist).filter(contains.c.playlist_id == playlist.playlist_id).all()
    report = Report.query.filter_by(party_id=party_id).filter_by(accepted=0).all()
    for r in report:
        song_id = r.song_id
        song = Song.query.filter_by(song_id=song_id).first()
        if song in playlist_songs:
            continue
        else:
            reqs[song] = r.requests
    return reqs

def report_accepts(party_id):
    accepts = dict()
    report = Report.query.filter_by(party_id=party_id).filter_by(accepted=1).all()
    party = Party.query.filter_by(party_id=party_id).first()
    playlist = Playlist.query.join(plays).join(Party).filter(plays.c.party_id == party.party_id).first()
    playlist_songs = Song.query.join(contains).join(Playlist).filter(contains.c.playlist_id == playlist.playlist_id).all()
    for r in report:
        song_id = r.song_id
        song = Song.query.filter_by(song_id=song_id).first()
        if song in playlist_songs:
            continue
        else:
            accepts[song] = r.requests
    return accepts

def get_users(song_id):
    song = Song.query.filter_by(song_id=song_id).first()
    users = User.query.join(requests).join(Song).filter(requests.c.song_id == song.song_id).all()
    return users

def get_accepted_songs(id):
    song_list = []
    user = User.query.filter_by(id=id).first()
    songs = Song.query.join(requests).join(User).filter(requests.c.id == user.id).all()
    for i in songs:
        if i.song_played==1:
            song_list.append(i)
    return song_list

def get_playlist_songs(playlist_id):
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    songs = Song.query.join(contains).join(Playlist).filter(contains.c.playlist_id == playlist.playlist_id).all()
    return songs

def get_dj_playlist(id):
    user = User.query.filter_by(id=id).first()
    playlist = Playlist.query.join(adds).join(User).filter(adds.c.id == user.id).all()
    return playlist

def get_report_data(party_id):
    report_dict = dict()
    report = Report.query.filter_by(party_id=party_id).all()
    for r in report:
        report_dict[r.song_id]=r.requests
    return report_dict

def delete_requests():
    users = User.query.all()
    for user in users:
        sql = 'DELETE FROM requests WHERE id='+str(user.id)+';'
        db.engine.execute(sql)
        db.session.commit()
    songs = Song.query.all()
    for song in songs:
        sql = 'UPDATE song SET song_played='+str(0)+',score='+str(0)+' WHERE song_id='+str(song.song_id)+';'
        db.engine.execute(sql)
        db.session.commit()

def close_party():
    party = Party.query.all()
    for p in party:
        p.party_on = 0
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.user_type == 'Dj':
        flash("You do not have persmission to access that page")
        return redirect(url_for('createparty'))
    form = SearchSongForm()
    party = Party.query.order_by(Party.party_id.desc()).first()

    if party==None:
        return render_template('partyover.html')
    elif party.party_on==0:
        return render_template('partyover.html')

    if form.validate_on_submit():
        if party.party_on==0:
            return render_template('partyover.html')
        song_name = form.song_name.data
        if form.song_name.data != "":
            song_name = clean_song_name(form.song_name.data)
            song = Song.query.filter_by(song_name=song_name).all()
            if song == []:
                all_songs = get_requested_songs(current_user.id)
                song = Song.query.filter_by(song_artist=song_name).all()
                song = list(set(song)-set(all_songs))
                if song == []:
                    song = Song.query.filter_by(song_genre=song_name).all()
                    song = list(set(song)-set(all_songs))
                    if song == []:
                        flash('No results found')
                        return render_template('index2.html', form=form, requested_songs=get_requested_songs(current_user.id))
                    else:
                        return render_template('index2.html', form=form, songs=song, requested_songs=get_requested_songs(current_user.id))
                else:
                    return render_template('index2.html', form=form, songs=song, requested_songs=get_requested_songs(current_user.id))
            else:
                all_songs = get_requested_songs(current_user.id)
                for i in all_songs:
                    if i.song_name == song[0].song_name:
                        flash('You have already requested this song!')
                        return render_template('index2.html', form=form, requested_songs=get_requested_songs(current_user.id))
                return render_template('index2.html', form=form, songs=song, requested_songs=get_requested_songs(current_user.id))
        else:
            flash("Please enter some information for the song search")
            return render_template('index2.html', form=form, requested_songs=get_requested_songs(current_user.id))
    return render_template('index.html',form=form, requested_songs=get_requested_songs(current_user.id))

@app.route('/djhome/<playlist_id>', methods=['GET', 'POST'])
@login_required
def djhome(playlist_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    form = SearchSongForm2()
    party = Party.query.order_by(Party.party_id.desc()).first()
    party.party_on = 1
    db.session.commit()
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    party.plays_the.append(playlist)
    db.session.commit()
    playlist_songs = get_playlist_songs(playlist_id)

    if form.validate_on_submit():
        song_name = form.song_name.data
        if song_name != "":
            song_name = clean_song_name(song_name)
            song = Song.query.filter_by(song_name=song_name).first()
            if song != None:
                playlist.contains_the.append(song)
                db.session.commit()
                return redirect(url_for('djhome',playlist_id=playlist.playlist_id))
            else:
                flash("Song Does not exist")
                return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)
        else:
            flash("Enter a song to be added to playlist")
            return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)

    return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)

@app.route('/dj/<playlist_id>/<song_id>', methods=['GET', 'POST'])
@login_required
def dj(playlist_id,song_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    form = SearchSongForm2()
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    playlist_songs = get_playlist_songs(playlist_id)
    song = Song.query.filter_by(song_id=song_id).first()
    song.song_played=1
    db.session.commit()
    affected_users = get_users(song_id)
    for user in affected_users:
        if user.accepted is None:
            user.accepted=1
        else:
            accepted = user.accepted
            user.accepted = accepted+1
        db.session.commit()
    party = Party.query.order_by(Party.party_id.desc()).first()
    report = Report.query.filter_by(song_id=song_id).filter_by(party_id=party.party_id).first()
    report.accepted = 1
    db.session.commit()

    if form.validate_on_submit():
        song_name = form.song_name.data
        if song_name != "":
            song_name = clean_song_name(song_name)
            song = Song.query.filter_by(song_name=song_name).first()
            if song != None:
                playlist.contains_the.append(song)
                db.session.commit()
                return redirect(url_for('djhome',playlist_id=playlist.playlist_id))
            else:
                flash("Song Does not exist")
                return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)
        else:
            flash("Enter a song to be added to playlist")
            return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)

    return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)


@app.route('/djreject/<playlist_id>/<song_id>', methods=['GET', 'POST'])
@login_required
def djreject(playlist_id,song_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    form = SearchSongForm2()
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    playlist_songs = get_playlist_songs(playlist_id)
    song = Song.query.filter_by(song_id=song_id).first()
    song.song_played=2
    db.session.commit()
    party = Party.query.order_by(Party.party_id.desc()).first()
    report = Report.query.filter_by(song_id=song_id).filter_by(party_id=party.party_id).first()
    report.accepted = 2
    db.session.commit()

    if form.validate_on_submit():
        song_name = form.song_name.data
        if song_name != "":
            song_name = clean_song_name(song_name)
            song = Song.query.filter_by(song_name=song_name).first()
            if song != None:
                playlist.contains_the.append(song)
                db.session.commit()
                return redirect(url_for('djhome',playlist_id=playlist.playlist_id))
            else:
                flash("Song Does not exist")
                return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)
        else:
            flash("Enter a song to be added to playlist")
            return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)

    return render_template('djhome.html',songs=get_top_requests(party.party_id),playlist=playlist,playlist_songs=playlist_songs,party=party,accepts=get_dj_accepts(party.party_id),form=form)




@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        if user.user_type == 'User':
            return redirect(url_for('index'))
        else:
            return redirect(url_for('createparty'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user_type = form.user_type.data
        user = User(username=form.username.data, email=form.email.data, user_type=user_type)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        login_user(user)
        if user_type=='User':
            return redirect(url_for('index'))
        else:
            return redirect(url_for('createparty'))
    return render_template('register.html', title='Register', form=form)

@app.route('/addsong', methods=['GET', 'POST'])
@login_required
def addsong():
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    form = AddSongForm()
    if form.validate_on_submit():
        song = Song(song_name=form.song_name.data, song_artist=form.song_artist.data, song_genre=form.song_genre.data, song_played=0, score=0)
        db.session.add(song)
        db.session.commit()
        flash('Successfully added song!')
        return redirect(url_for('allsongs'))
    return render_template('addsong.html', form=form)

@app.route('/allsongs')
@login_required
def allsongs():
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    return render_template('allsongs.html', songs=Song.query.all())

@app.route('/songrequests')
@login_required
def songrequests():
    if current_user.user_type == 'Dj':
        flash("You do not have persmission to access that page")
        return redirect(url_for('createparty'))
    return render_template('songrequests.html',songs=get_requested_songs(current_user.id))

@app.route('/songaccepts')
@login_required
def songaccepts():
    if current_user.user_type == 'Dj':
        flash("You do not have persmission to access that page")
        return redirect(url_for('createparty'))
    return render_template('songaccepts.html',songs=get_accepted_songs(current_user.id))

@app.route('/request/<song_id>', methods=['GET', 'POST'])
@login_required
def request(song_id):
    if current_user.user_type == 'Dj':
        flash("You do not have persmission to access that page")
        return redirect(url_for('createparty'))

    form = SearchSongForm()
    user = User.query.filter_by(id=current_user.id).first()
    song = Song.query.filter_by(song_id=song_id).first()
    song.requested_by.append(user)
    db.session.commit()
    if user.attempts is None:
        user.attempts = 1
    else:
        attempts = user.attempts
        user.attempts = attempts+1
    db.session.commit()
    score = song.score
    song.score = score+1
    db.session.commit()
    party = Party.query.order_by(Party.party_id.desc()).first()
    report = Report.query.filter_by(song_id=song_id).filter_by(party_id=party.party_id).first()
    if report is None:
        report = Report(party_id=party.party_id,song_id=song_id,requests=1,accepted=0)
        db.session.add(report)
        db.session.commit()
    else:
        count = report.requests
        count += 1
        report.requests = count
        db.session.commit()
    if party==None:
        return render_template('partyover.html')
    elif party.party_on==0:
        return render_template('partyover.html')

    if form.validate_on_submit():
        if party.party_on==0:
            return render_template('partyover.html')
        song_name = form.song_name.data
        if form.song_name.data != "":
            song_name = clean_song_name(form.song_name.data)
            song = Song.query.filter_by(song_name=song_name).all()
            if song == []:
                all_songs = get_requested_songs(current_user.id)
                song = Song.query.filter_by(song_artist=song_name).all()
                song = list(set(song)-set(all_songs))
                if song == []:
                    song = Song.query.filter_by(song_genre=song_name).all()
                    song = list(set(song)-set(all_songs))
                    if song == []:
                        flash('No results found')
                        return render_template('index2.html', form=form, requested_songs=get_requested_songs(current_user.id))
                    else:
                        return render_template('index2.html', form=form, songs=song, requested_songs=get_requested_songs(current_user.id))
                else:
                    return render_template('index2.html', form=form, songs=song, requested_songs=get_requested_songs(current_user.id))
            else:
                all_songs = get_requested_songs(current_user.id)
                for i in all_songs:
                    if i.song_name == song[0].song_name:
                        flash('You have already requested this song!')
                        return render_template('index2.html', form=form, requested_songs=get_requested_songs(current_user.id))
                return render_template('index2.html', form=form, songs=song, requested_songs=get_requested_songs(current_user.id))
        else:
            flash("Please enter some information for the song search")
            return render_template('index2.html', form=form, requested_songs=get_requested_songs(current_user.id))
    return render_template('index2.html', form=form, requested_songs=get_requested_songs(current_user.id))

@app.route('/createplaylist', methods=['GET', 'POST'])
@login_required
def createplaylist():
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    form = CreatePlaylistForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        playlist = Playlist(playlist_name=form.playlist_name.data)
        db.session.add(playlist)
        db.session.commit()
        playlist.added_by.append(user)
        db.session.commit()
        flash('Successfully created playlist!')
        return redirect(url_for('songlist',playlist_id=playlist.playlist_id))
    return render_template('createplaylist.html', form=form)

@app.route('/songlist/<playlist_id>', methods=['GET', 'POST'])
@login_required
def songlist(playlist_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    final_songs = []
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    songs_in_playlist = Song.query.join(contains).join(Playlist).filter(contains.c.playlist_id == playlist.playlist_id).all()
    all_songs = Song.query.all()
    for song in all_songs:
        if song in songs_in_playlist:
            continue
        else:
            final_songs.append(song)
    return render_template('songlist.html', songs=final_songs, playlist=playlist)

@app.route('/addsongtoplaylist/<playlist_id>/<song_id>', methods=['GET', 'POST'])
@login_required
def addsongtoplaylist(playlist_id,song_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    final_songs = []
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    song = Song.query.filter_by(song_id=song_id).first()
    playlist.contains_the.append(song)
    db.session.commit()
    song_check = Song.query.join(contains).join(Playlist).filter(contains.c.playlist_id == playlist.playlist_id).all()
    all_songs = Song.query.all()
    for song in all_songs:
        if song in song_check:
            continue
        else:
            final_songs.append(song)
    flash('Successfully added song in playlist!')
    return render_template('songlist.html', songs=final_songs, playlist=playlist)

@app.route('/allplaylist')
@login_required
def allplaylist():
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    return render_template('allplaylist.html',playlist=get_dj_playlist(current_user.id))

@app.route('/playlistsongs/<playlist_id>')
@login_required
def playlistsongs(playlist_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    party = Party.query.order_by(Party.party_id.desc()).first()
    if party is not None:
        party_present = party.party_on
    else:
        party_present = 0
    return render_template('playlistsongs.html',songs=get_playlist_songs(playlist.playlist_id),playlist=playlist,party_present=party_present)

@app.route('/deletesonginplaylist/<playlist_id>/<song_id>', methods=['GET', 'POST'])
@login_required
def deletesonginplaylist(playlist_id,song_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    sql = 'DELETE FROM contains WHERE playlist_id='+playlist_id+' AND song_id='+song_id+';'
    db.engine.execute(sql)
    db.session.commit()
    flash ("Song Deleted from Playlist!")
    party = Party.query.order_by(Party.party_id.desc()).first()
    if party is not None:
        party_present = party.party_on
    else:
        party_present = 0
    return render_template('playlistsongs.html', songs=get_playlist_songs(playlist.playlist_id),playlist=playlist,party_present=party_present)

@app.route('/deleteplaylist/<playlist_id>', methods=['GET', 'POST'])
@login_required
def deleteplaylist(playlist_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    test = Playlist.query.join(plays).join(Party).filter(plays.c.playlist_id == playlist.playlist_id).all()
    if test is not None:
        flash("Cannot Delete Playlist because it is used in an existing report")
        return redirect(url_for('allplaylist'))
    sql = 'DELETE FROM contains WHERE playlist_id='+playlist_id+';'
    db.engine.execute(sql)
    db.session.commit()
    sql = 'DELETE FROM playlist WHERE playlist_id='+playlist_id+';'
    db.engine.execute(sql)
    db.session.commit()
    flash ("Playlist Deleted!")
    return render_template('allplaylist.html', playlist=get_dj_playlist(current_user.id))

@app.route('/chooseplaylist')
@login_required
def chooseplaylist():
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    return render_template('chooseplaylist.html')

@app.route('/djplaylist')
@login_required
def djplaylist():
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    return render_template('djplaylist.html',playlist=get_dj_playlist(current_user.id))

@app.route('/songautocomplete')
def songdict():
    res = Song.query.all()
    list_songs = [r.as_dict() for r in res]

    list_songs_genre = []
    res = Song.query.all()
    for r in res:
        if r.as_dict_genre() in list_songs_genre:
            continue
        else:
            list_songs_genre.append(r.as_dict_genre())

    list_songs_artist = []
    res = Song.query.all()
    for r in res:
        if r.as_dict_artist() in list_songs_artist:
            continue
        else:
            list_songs_artist.append(r.as_dict_artist())

    query_results = list_songs + list_songs_genre + list_songs_artist
    return jsonify(query_results)

@app.route('/songautocomplete2')
def songdict2():
    res = Song.query.all()
    list_songs = [r.as_dict() for r in res]
    return jsonify(list_songs)

@app.route('/createparty', methods=['GET', 'POST'])
@login_required
def createparty():
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    last_party = Party.query.order_by(Party.party_id.desc()).first()
    if last_party is not None:
        if last_party.party_on==1 or last_party.party_on==2:
            playlist_chosen = Playlist.query.join(plays).join(Party).filter(plays.c.party_id == last_party.party_id).first()
            if playlist_chosen is None:
                return redirect(url_for('chooseplaylist'))
            else:
                return redirect(url_for('djhome',playlist_id=playlist_chosen.playlist_id))
    form = CreatePartyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        close_party()
        party = Party(party_name=form.party_name.data,party_on=2)
        db.session.add(party)
        db.session.commit()
        party.created_by.append(user)
        db.session.commit()
        flash('Successfully created party!')
        return redirect(url_for('chooseplaylist'))
    return render_template('createparty.html',form=form)

@app.route('/report/<party_id>/<playlist_id>')
@login_required
def report(party_id,playlist_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    accepted_requests=report_accepts(party_id)
    pending_requests=report_requests(party_id)
    party = Party.query.filter_by(party_id=party_id).first()
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    return render_template('report.html', party=party,playlist=playlist,songs_in_playlist=get_playlist_songs(playlist_id),accepted_requests=accepted_requests,pending_requests=pending_requests,recommendations=recommend_songs(party_id))

@app.route('/stopparty/<party_id>/<playlist_id>')
@login_required
def stopparty(party_id,playlist_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    accepted_requests=report_accepts(party_id)
    pending_requests=report_requests(party_id)
    party = Party.query.filter_by(party_id=party_id).first()
    parties = Party.query.all()
    for p in parties:
        p.party_on = 0
        db.session.commit()
    delete_requests()
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    return render_template('report.html', party=party,playlist=playlist,songs_in_playlist=get_playlist_songs(playlist_id),accepted_requests=accepted_requests,pending_requests=pending_requests,recommendations=recommend_songs(party_id))


@app.route('/allreports')
@login_required
def allreports():
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    report_dict = dict()
    report = Report.query.all()
    for r in report:
        party = Party.query.filter_by(party_id=r.party_id).first()
        if party not in report_dict:
            playlist = Playlist.query.join(plays).join(Party).filter(plays.c.party_id == party.party_id).first()
            report_dict[party] = playlist.playlist_id
    return render_template('allreports.html',reports=report_dict)

@app.route('/editplaylist/<party_id>/<playlist_id>/<song_id>')
@login_required
def editplaylist(party_id,playlist_id,song_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    song = Song.query.filter_by(song_id=song_id).first()
    playlist.contains_the.append(song)
    db.session.commit()
    party = Party.query.filter_by(party_id=party_id).first()
    accepted_requests=report_accepts(party_id)
    pending_requests=report_requests(party_id)
    return render_template('report.html', party=party,playlist=playlist,songs_in_playlist=get_playlist_songs(playlist_id),accepted_requests=accepted_requests,pending_requests=pending_requests,recommendations=recommend_songs(party_id))

@app.route('/editplaylist2/<party_id>/<playlist_id>/<song_id>')
@login_required
def editplaylist2(party_id,playlist_id,song_id):
    if current_user.user_type == 'User':
        flash("You do not have persmission to access that page")
        return redirect(url_for('index'))
    playlist = Playlist.query.filter_by(playlist_id=playlist_id).first()
    song = Song.query.filter_by(song_id=song_id).first()
    sql = 'DELETE FROM contains WHERE playlist_id='+playlist_id+' AND song_id='+song_id+';'
    db.engine.execute(sql)
    db.session.commit()
    flash ("Song Deleted from Playlist!")
    party = Party.query.filter_by(party_id=party_id).first()
    accepted_requests=report_accepts(party_id)
    pending_requests=report_requests(party_id)
    return render_template('report.html', party=party,playlist=playlist,songs_in_playlist=get_playlist_songs(playlist_id),accepted_requests=accepted_requests,pending_requests=pending_requests,recommendations=recommend_songs(party_id))

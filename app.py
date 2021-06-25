# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import datetime as datetime_now
import logging
import sys
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from flask_migrate import Migrate
from flask_moment import Moment
from sqlalchemy import func

from forms import *
from models import *
from models import db

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

# connect to a local postgresql database
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

# noinspection PyUnresolvedReferences
def format_datetime(value, date_format='medium'):
    date = dateutil.parser.parse(value)
    if date_format == 'full':
        date_format = "EEEE MMMM, d, y 'at' h:mma"
    elif date_format == 'medium':
        date_format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, date_format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    venues_city = Venue.query.distinct(Venue.city)
    current_time = datetime_now.datetime.utcnow()
    for venue in venues_city:
        venues_list = []
        city = venue.city
        venues_by_city = Venue.query.filter_by(city=city).all()
        for all_venues in venues_by_city:
            venue_id = all_venues.id
            num_upcoming_shows = Show.query.filter_by(venue_id=venue_id).filter(
                current_time < Show.date) \
                .count()
            venues_list.append({
                "id": venue_id,
                "name": all_venues.name,
                "num_upcoming_shows": num_upcoming_shows
            })
        data.append({
            "city": city,
            "state": venue.state,
            "venues": venues_list
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '').strip()
    data_list = []
    current_time = datetime_now.datetime.utcnow()
    for venu in Venue.query.filter(func.lower(Venue.name).contains(search_term.lower())).all():
        data_list.append({
            "id": venu.id,
            "name": venu.name,
            "num_upcoming_shows": Show.query.filter_by(venue_id=venu.id).filter(
                current_time < Show.date).count()
        })
    response = {
        "count": len(data_list),
        "data": data_list
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    data = {}
    try:
        venue = Venue.query.filter_by(id=venue_id).first()
        current_time = datetime_now.datetime.utcnow()
        # Get genres list
        genres_list = []
        for genre in venue.genres:
            genres_list.append(genre.name)
        # Get past shows list
        past_shows_list = []
        for show in Show.query.filter_by(venue_id=venue_id).filter(current_time > Show.date).all():
            artist = show.artist
            past_shows_list.append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            })

        # Get upcoming shows list
        upcoming_shows_list = []
        for show in Show.query.filter_by(venue_id=venue_id).filter(current_time < Show.date).all():
            artist = show.artist
            upcoming_shows_list.append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            })
        data = {
            "id": venue_id,
            "name": venue.name,
            "genres": genres_list,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows_list,
            "upcoming_shows": upcoming_shows_list,
            "past_shows_count": len(past_shows_list),
            "upcoming_shows_count": len(upcoming_shows_list)
        }
    except:
        print(sys.exc_info())
        abort(500)
    finally:
        db.session.close()
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        newVenue = Venue(
            name=request.form.get('name'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            image_link=request.form.get('image_link'),
            facebook_link=request.form.get('facebook_link'),
            website=request.form.get('website_link'),
            seeking_talent=request.form.get('seeking_talent') == "y",
            seeking_description=request.form.get('seeking_description'),
        )
        db.session.add(newVenue)
        genres_list = []
        for genre_name in request.form.getlist('genres'):
            query = Genre.query.filter_by(name=genre_name)
            if query.count() > 0:
                genres_list.append(query.first())
            else:
                genres_list.append(Genre(name=genre_name))
        newVenue.genres = genres_list
        db.session.commit()
        flash('Venue ' + newVenue.name + ' was successfully listed!')
    except:
        flash('An error occurred. Venue ' + request.form.get('name') + ' could not be listed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        query = Venue.query.filter_by(id=venue_id)
        if query.count() > 0:
            venue = query.first()
            flash(venue.name + " venue has been deleted.")
            db.session.delete(venue)
            db.session.commit()
        else:
            flash("This venue doesn't exist.")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("An error occurred. Venue could not be deleted.")
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # Done
    # clicking that button delete it from the db then redirect the user to the homepage
    # Done
    return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists_list = Artist.query.all()
    data = []
    for artist in artists_list:
        data.append({
            "id": artist.id,
            "name": artist.name,
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '').strip()
    data_list = []
    current_time = datetime_now.datetime.utcnow()
    for artist in Artist.query.filter(func.lower(Artist.name).contains(search_term.lower())).all():
        data_list.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": Show.query.filter_by(artist_id=artist.id).filter(
                current_time < Show.date).count()
        })
    response = {
        "count": len(data_list),
        "data": data_list
    }
    print(response)
    return render_template('pages/search_artists.html', results=response,
                           search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    data = {}
    try:
        artist = Artist.query.filter_by(id=artist_id).first()
        current_time = datetime_now.datetime.utcnow()
        # Get genres list
        genres_list = []
        for genre in artist.genres:
            genres_list.append(genre.name)
        # Get past shows list
        past_shows_list = []
        for show in Show.query.filter_by(artist_id=artist_id).filter(current_time > Show.date).all():
            venue = show.venue
            past_shows_list.append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": show.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            })

        # Get upcoming shows list
        upcoming_shows_list = []
        for show in Show.query.filter_by(artist_id=artist_id).filter(current_time < Show.date).all():
            venue = show.venue
            upcoming_shows_list.append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": show.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            })

        data = {
            "id": artist_id,
            "name": artist.name,
            "genres": genres_list,
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": past_shows_list,
            "upcoming_shows": upcoming_shows_list,
            "past_shows_count": len(past_shows_list),
            "upcoming_shows_count": len(upcoming_shows_list)
        }
    except:
        print(sys.exc_info())
        abort(500)
    finally:
        db.session.close()
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_data = Artist.query.filter_by(id=artist_id).first()  # type: Artist
    # Get genres list
    genres_list = []
    for genre in artist_data.genres:
        genres_list.append(genre.name)
    artist = {
        "id": artist_id,
        "name": artist_data.name,
        "genres": genres_list,
        "city": artist_data.city,
        "state": artist_data.state,
        "phone": artist_data.phone,
        "website": artist_data.website,
        "facebook_link": artist_data.facebook_link,
        "seeking_venue": artist_data.seeking_venue,
        "seeking_description": artist_data.seeking_description,
        "image_link": artist_data.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    try:
        artist = Artist.query.filter_by(id=artist_id).first()
        artist.name = request.form.get('name')
        artist.city = request.form.get('city')
        artist.state = request.form.get('state')
        artist.phone = request.form.get('phone')
        artist.image_link = request.form.get('image_link')
        artist.facebook_link = request.form.get('facebook_link')
        artist.website = request.form.get('website_link')
        artist.seeking_venue = request.form.get('seeking_venue') == "y"
        artist.seeking_description = request.form.get('seeking_description')
        genres_new_list = []
        for genre_name in request.form.getlist('genres'):
            query = Genre.query.filter_by(name=genre_name)
            if query.count() > 0:
                genres_new_list.append(query.first())
            else:
                genres_new_list.append(Genre(name=genre_name))
        artist.genres = genres_new_list
        db.session.commit()
        flash("Artist " + request.form.get('name') + " has been updated.")
    except:
        flash('An error occurred. Artist could not be updated.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue_data = Venue.query.filter_by(id=venue_id).first()  # type: Venue
    # Get genres list
    genres_list = []
    for genre in venue_data.genres:
        genres_list.append(genre.name)
    venue = {
        "id": venue_data.id,
        "name": venue_data.name,
        "genres": genres_list,
        "address": venue_data.address,
        "city": venue_data.city,
        "state": venue_data.state,
        "phone": venue_data.phone,
        "website": venue_data.website,
        "facebook_link": venue_data.facebook_link,
        "seeking_talent": venue_data.seeking_talent,
        "seeking_description": venue_data.seeking_description,
        "image_link": venue_data.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.filter_by(id=venue_id).first()  # type: Venue
        venue.name = request.form.get('name')
        venue.city = request.form.get('city')
        venue.state = request.form.get('state')
        venue.address = request.form.get('address')
        venue.phone = request.form.get('phone')
        venue.image_link = request.form.get('image_link')
        venue.facebook_link = request.form.get('facebook_link')
        venue.website = request.form.get('website_link')
        venue.seeking_talent = request.form.get('seeking_talent') == "y"
        venue.seeking_description = request.form.get('seeking_description')
        genres_new_list = []
        for genre_name in request.form.getlist('genres'):
            query = Genre.query.filter_by(name=genre_name)
            if query.count() > 0:
                genres_new_list.append(query.first())
            else:
                genres_new_list.append(Genre(name=genre_name))
        venue.genres = genres_new_list
        db.session.commit()
        flash("Venue " + request.form.get('name') + " has been updated.")
    except:
        flash('An error occurred. Venue could not be updated.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        newArtist = Artist(
            name=request.form.get('name'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            phone=request.form.get('phone'),
            image_link=request.form.get('image_link'),
            facebook_link=request.form.get('facebook_link'),
            website=request.form.get('website_link'),
            seeking_venue=request.form.get('seeking_venue') == "y",
            seeking_description=request.form.get('seeking_description'),
        )
        db.session.add(newArtist)
        genres_list = []
        for genre_name in request.form.getlist('genres'):
            query = Genre.query.filter_by(name=genre_name)
            if query.count() > 0:
                genres_list.append(query.first())
            else:
                genres_list.append(Genre(name=genre_name))
        newArtist.genres = genres_list
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + newArtist.name + ' was successfully listed!')
    except:
        flash('An error occurred. Artist ' + request.form.get('name') + ' could not be listed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows_list = db.session.query(Show).join(Venue).join(Artist).all()
    data = []
    for show in shows_list:
        venue = show.venue
        artist = show.artist
        data.append({
            "venue_id": venue.id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        artist_id = int(request.form.get('artist_id'))
        venue_id = int(request.form.get('venue_id'))
        start_time = request.form.get('start_time')
        db.session.add(Show(artist_id=artist_id,
                            venue_id=venue_id,
                            date=start_time)
                       )
        db.session.commit()
        flash('Show was successfully listed!')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    except:
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import collections
from datetime import datetime
from flask import (
    Flask, 
    render_template, 
    request, 
    Response, 
    flash, 
    redirect, 
    url_for,
    abort
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form, FlaskForm
from forms import *
from models import db, Venue, Artist, Shows

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

collections.Callable = collections.abc.Callable
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

# Done: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # Done?: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  locals = []
  venues = Venue.query.all()

  places = Venue.query.distinct(Venue.city, Venue.state).all()

  for place in places:
      locals.append({
          'city': place.city,
          'state': place.state,
          'venues': [{
              'id': venue.id,
              'name': venue.name,
              'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.now()])
          } for venue in venues if
              venue.city == place.city and venue.state == place.state]
      })
  return render_template('pages/venues.html', areas=locals)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%')).all()
  data = []
  for venue in venues:
    upcoming_shows = 0

    for show in venue.shows:
      if (show.start_time > datetime.now()):
        upcoming_shows += 1
    venue_dict = {
      'id': venue.id,
      'name': venue.name,
      'upcoming_shows': upcoming_shows
    }
    data.append(venue_dict)

  response={
    'count': len(venues),
    'data': data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # Done: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get_or_404(venue_id)

  past_shows = []
  upcoming_shows = []

  for show in venue.shows:
    artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show.artist_id).one()
    theshow = {
      'artist_id': show.artist_id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(show.start_time)
      }

    if (show.start_time < datetime.now()):
      past_shows.append(theshow)
    else:
      upcoming_shows.append(theshow)

  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website_link,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  # Done: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  v_id = db.session.query(Venue).filter_by(id=venue_id).one()
  to_delete = v_id
  try:
    db.session.delete(to_delete)
    db.session.commit()
    flash('Venue sucessfully deleted!')
  except:
    db.session.rollback()
    flash('Venue could not be deleted.')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # Done: insert form data as a new Venue record in the db, instead
  # Done: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  error = False

  if form.validate():
    try:
      new_venue = Venue()
      form.populate_obj(new_venue)
      db.session.add(new_venue)
      db.session.commit()
    except:
      error=True
      db.session.rollback()
      flash('There was a problem adding this Venue, please try again.')
    finally:
      db.session.close()
    if error:
      abort(400)
    else:
    # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # Done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')
  else:
    for field, message in form.errors.items():
      error = True
      flash(field + ' - ' + str(message), 'danger')
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  edit_venue = Venue.query.filter_by(id=venue_id).one()
  form.name.data = edit_venue.name
  form.city.data = edit_venue.city
  form.state.data = edit_venue.state
  form.address.data = edit_venue.address
  form.phone.data = edit_venue.phone
  form.genres.data = edit_venue.genres
  form.image_link.data = edit_venue.image_link
  form.facebook_link.data = edit_venue.facebook_link
  form.website_link.data = edit_venue.website_link
  form.seeking_talent.data = edit_venue.seeking_talent
  form.seeking_description.data = edit_venue.seeking_description

  # Done: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=edit_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # Done: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  error = False

  if form.validate():
    try:
      edit_venue = Venue.query.filter_by(id=venue_id).one()
      form.populate_obj(edit_venue)
      db.session.commit()
    except:
      db.session.rollback()
      flash('Unable to update Venue!')
    finally:
      db.session.close()
      flash('Venue was successfully updated!')
      return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    for field, message in form.errors.items():
      error = True
      flash(field + ' - ' + str(message), 'danger')
    return redirect(url_for('edit_venue', venue_id=venue_id))
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # Done: replace with real data returned from querying the database
  locals = []
  artists = Artist.query.all()

  for artist in artists:
    upcoming_shows = []

    for show in artist.shows:
      venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id == show.venue_id).one()
      theshow = {
        'venue_id': show.venue_id,
        'venue_name': venue.name,
        'venue_image_link': venue.image_link,
        'start_time': str(show.start_time)
      }
      if (show.start_time >= datetime.now()):
        upcoming_shows.append(theshow)
      
    locals.append({
        'id': artist.id,
        'name': artist.name,
        'num_upcoming_shows': len(upcoming_shows)
    })
  return render_template('pages/artists.html', artists=locals)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
  data = []
  for artist in artists:
    upcoming_shows = 0

    for show in artist.shows:
      if (show.start_time > datetime.now()):
        upcoming_shows += 1
    artist_dict = {
      'id': artist.id,
      'name': artist.name,
      'upcoming_shows': upcoming_shows,
    }
    data.append(artist_dict)
  response ={
    'count': len(artists),
    'data': data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given aritst_id
  artist = Artist.query.get(artist_id)

  past_shows = []
  upcoming_shows = []

  for show in artist.shows:
    venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id == show.venue_id).one()
    theshow = {
      'venue_id': show.venue_id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': str(show.start_time)
      }

    if (show.start_time < datetime.now()):
      past_shows.append(theshow)
    else:
      upcoming_shows.append(theshow)

  data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website_link,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

@app.route('/artists/<artist_id>', methods=['POST'])
def delete_artist(artist_id):
  # Done: Complete this endpoint for taking a artist_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  a_id = db.session.query(Artist).filter_by(id=artist_id).one()
  to_delete = a_id
  try:
    db.session.delete(to_delete)
    db.session.commit()
    flash('Artist sucessfully deleted!')
  except:
    db.session.rollback()
    flash('Artist could not be deleted.')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Artist on a Artist Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  edit_artist = Artist.query.filter_by(id=artist_id).one()
  form.name.data = edit_artist.name
  form.city.data = edit_artist.city
  form.state.data = edit_artist.state
  form.phone.data = edit_artist.phone
  form.genres.data = edit_artist.genres
  form.image_link.data = edit_artist.image_link
  form.facebook_link.data = edit_artist.facebook_link
  form.website_link.data = edit_artist.website_link
  form.seeking_venue.data = edit_artist.seeking_venue
  form.seeking_description.data = edit_artist.seeking_description

  # Done: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=edit_artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # Done: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  error = False

  if form.validate():
    try:
      edit_artist = Artist.query.filter_by(id=artist_id).one()
      form.populate_obj(edit_artist)
      db.session.commit()
    except:
      db.session.rollback()
      flash('Unable to update Artist!')
    finally:
      db.session.close()
      flash('Artist was successfully updated!')
      return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    for field, message in form.errors.items():
      flash(field + ' - ' + str(message), 'danger')
    return redirect(url_for('edit_artist', artist_id=artist_id))

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # done: insert form data as a new Venue record in the db, instead
  # done: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  error = False

  if form.validate():
    try:
      new_artist = Artist()
      form.populate_obj(new_artist)
      db.session.add(new_artist)
      db.session.commit()
    except:
      error=True
      db.session.rollback()
      flash('There was a problem adding this Artist, please try again.')
    finally:
      db.session.close()
    if error:
      abort(400)
    else:
    # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # done: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')
  else:
    for field, message in form.errors.items():
      flash(field + ' - ' + str(message), 'danger')
    return render_template('forms/new_artist.html', form=form)

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # Done: replace with real venues data.
  # num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  shows = db.session.query(Venue.name, Artist.name, Artist.image_link, Shows.venue_id, Shows.artist_id, Shows.start_time)\
    .filter(Venue.id==Shows.venue_id, Artist.id==Shows.artist_id)
  for show in shows:
    show_dict = {
      'venue_name': show[0],
      'artist_name': show[1],
      'artist_image_link': show[2],
      'venue_id': show[3],
      'artist_id': show[4],
      'start_time': str(show[5])
    }
    data.append(show_dict)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # Done: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  error = False
  
  try:
    show = Shows()
    form.populate_obj(show)
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    flash('Error! Show was not created.')
  finally:
    db.session.close()
  # on successful db insert, flash success
    flash('Show was successfully listed!')
  # Done: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

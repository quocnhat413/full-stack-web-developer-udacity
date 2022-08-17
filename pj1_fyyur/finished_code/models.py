from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    # Done: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Shows', backref=db.backref('Venue'), lazy='joined', cascade="all, delete-orphan")

    def __repr__(self):
      return f'<Venue {self.id}, {self.name}>'

    def get_past_shows(self):
      past_shows = []
      for show in self.shows:
        if show.start_time <= datetime.now():
          past_shows.append(show)
      return past_shows
    
    def get_upcoming_shows(self):
      upcoming_shows = []
      for show in self.shows:
        if show.start_time > datetime.now():
          upcoming_shows.append(show)
      return upcoming_shows

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean())
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Shows', backref=db.backref('Artist'), lazy='joined', cascade="all, delete-orphan")

    def __repr__(self):
      return f'<Artist {self.id}, {self.name}>'
    # Done: implement any missing fields, as a database migration using Flask-Migrate
    #Many to Many relationship/association table

    def get_past_shows(self):
      past_shows = []
      for show in self.shows:
        if show.start_time <= datetime.now():
          past_shows.append(show)
      return past_shows
    
    def get_upcoming_shows(self):
      upcoming_shows = []
      for show in self.shows:
        if show.start_time > datetime.now():
          upcoming_shows.append(show)
      return upcoming_shows

class Shows(db.Model):
    __tablename__ = 'Shows'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(Venue.id), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id), nullable=False)
    start_time = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    def __repr__(self):
      return f'<Shows {self.id}>'

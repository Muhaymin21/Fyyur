from flask_sqlalchemy import SQLAlchemy

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
db = SQLAlchemy()


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='venue', lazy=True, cascade="all, delete-orphan")


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='artist', lazy=True, cascade="all, delete-orphan")


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)


artist_genre = db.Table('artist_genre',
                        db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id')),
                        db.Column('genre_name', db.String(120), db.ForeignKey('Genre.name')))

venue_genre = db.Table('venue_genre',
                       db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id')),
                       db.Column('genre_name', db.String(120), db.ForeignKey('Genre.name')))


class Genre(db.Model):
    __tablename__ = 'Genre'
    name = db.Column(db.String(120), primary_key=True)
    artist_genres = db.relationship('Artist', secondary=artist_genre,
                                    backref=db.backref('genres', lazy=True))
    venue_genres = db.relationship('Venue', secondary=venue_genre,
                                   backref=db.backref('genres', lazy=True))

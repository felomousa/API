import os
import requests
from flask import Flask, jsonify
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from dotenv import load_dotenv
import logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from flask_cors import CORS
from flask_migrate import Migrate
from finance import stockUp

load_dotenv()
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
apscheduler_logger = logging.getLogger('apscheduler')
apscheduler_logger.setLevel(logging.WARNING)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = os.getenv("SPOTIFY_SCOPE")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///media_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
scheduler = BackgroundScheduler()

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(200), nullable=False)
    album_name = db.Column(db.String(200), nullable=False)
    artist_name = db.Column(db.String(200), nullable=False)
    album_cover_url = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
class MovieLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    watched_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    poster_url = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.String(10), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
with app.app_context():
    db.create_all()

oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
)

def purge_old_entries():
    with app.app_context():
        try:
            latest_track = Track.query.order_by(Track.timestamp.desc()).first()
            if latest_track:
                Track.query.filter(Track.id != latest_track.id).delete()
                logging.info("Purged old tracks")
            latest_movie = MovieLog.query.order_by(MovieLog.timestamp.desc()).first()
            if latest_movie:
                MovieLog.query.filter(MovieLog.id != latest_movie.id).delete()
                logging.info("Purged old movie logs")
            latest_finance = Finance.query.order_by(Finance.price.desc()).first()  
            if latest_finance:
                Finance.query.filter(Finance.price != latest_finance.price).delete()
                logging.info("Purged old finance entries")
            db.session.commit()
            logging.info("Successfully purged all old entries from the databases.")

        except Exception as e:
            db.session.rollback()  
            logging.error(f"Error while purging old entries: {e}")
scheduler.add_job(purge_old_entries, 'interval', minutes=10)

def query_add_finance():
    with app.app_context():
        try:
            price = stockUp()
            new_finance_entry = Finance(price=price)
            db.session.add(new_finance_entry)
            db.session.commit()

            logging.info(f"Added new financial entry with price: {price}")
        except Exception as e:
            logging.error(f"Error adding finance data to database: {e}")
scheduler.add_job(query_add_finance, 'interval', minutes=5)

def query_spotify_and_add_track():
    with app.app_context():  
        try:
            token_info = oauth.get_cached_token()

            if not token_info:
                logging.info("No cached token found, unable to query Spotify.")
                return

            spotify_client = spotipy.Spotify(auth=token_info['access_token'])

            song_name, album_name, artist_name, album_cover_url = get_current_playing_info(spotify_client)

            if song_name is None:
                return

            existing_track = Track.query.order_by(Track.timestamp.desc()).first()

            if existing_track is None or existing_track.song_name != song_name:
                new_track = Track(
                song_name=song_name,
                album_name=album_name,
                artist_name=artist_name,
                album_cover_url=album_cover_url)
                db.session.add(new_track)
                db.session.commit()
                logging.info(f"Added new track to the database: {song_name} by {artist_name}.")

        except Exception as e:
            logging.error(f"Error querying Spotify API or adding track to database: {e}")
scheduler.add_job(query_spotify_and_add_track, 'interval', minutes=0.01, max_instances=2)

def scrape_netflix_and_add_movie_log():
    with app.app_context():  
        try:
            username = os.getenv("LETTERBOXD_USERNAME")
            if not username:
                logging.error("Letterboxd username is not set.")
                return

            url = f"https://letterboxd.com/{username}/films/diary/"
            response = requests.get(url)

            if response.status_code != 200:
                logging.error(f"Failed to fetch the Letterboxd page. Status code: {response.status_code}")
                return

            soup = BeautifulSoup(response.content, 'html.parser')

            diary_entries = soup.find_all('tr', class_='diary-entry-row')

            if not diary_entries:
                logging.error("No diary entries found on the page.")
                return

            first_entry = diary_entries[0]

            title_tag = first_entry.find('h3', class_='headline-3 prettify').find('a')
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                logging.error("Could not find the movie title.")
                return

            poster_tag = first_entry.find('img')
            if poster_tag:
                poster_url = poster_tag['src']
            else:
                poster_url = None

            rating_tag = first_entry.find('span', class_='rating')
            if rating_tag:
                rating = rating_tag.get_text(strip=True)
            else:
                logging.error("Could not find the movie rating.")
                rating = None

            existing_movie = MovieLog.query.filter_by(title=title).first()

            if not existing_movie:
                new_movie = MovieLog(
                    title=title,
                    poster_url=poster_url,
                    rating=rating
                )
                db.session.add(new_movie)
                db.session.commit()
                logging.info(f"Added new movie log: {title}.")
        except Exception as e:
            logging.error(f"Error scraping Letterboxd or adding movie log to the database: {e}")
scheduler.add_job(scrape_netflix_and_add_movie_log, 'interval', minutes=0.5)

scheduler.start()

def get_current_playing_info(spotify_client):
    try:

        current_track = spotify_client.current_user_playing_track()

        if current_track is None or 'item' not in current_track:
            return None, None, None, None

        song_name = current_track['item']['name']
        album_name = current_track['item']['album']['name']
        artist_name = ", ".join([artist['name'] for artist in current_track['item']['artists']])
        album_cover_url = current_track['item']['album']['images'][0]['url']

        return song_name, album_name, artist_name, album_cover_url

    except Exception as e:
        logging.error(f"Error fetching current playing info: {e}")
        return None, None, None, None

@app.route('/spotify')
def spotify_callback():
    try:
        latest_track = Track.query.order_by(Track.timestamp.desc()).first()

        if latest_track:
            return jsonify({
                "song_name": latest_track.song_name,
                "album_name": latest_track.album_name,
                "artist_name": latest_track.artist_name,
                "album_cover_url": latest_track.album_cover_url,
                "time_played": latest_track.timestamp
            }), 200
        else:
            return jsonify({"message": "No track found in the database"}), 404
    except Exception as e:
        return jsonify({"error": "Callback handling failed"}), 500

@app.route('/netflix')
def netflix_callback():
    try:

        latest_movie = MovieLog.query.order_by(MovieLog.timestamp.desc()).first()

        if latest_movie:
            return jsonify({
                "title": latest_movie.title,
                "poster_url": latest_movie.poster_url,
                "rating": latest_movie.rating
            }), 200
        else:
            return jsonify({"message": "No movie logs found in the database"}), 404
    except Exception as e:
        logging.error(f"Error handling Netflix callback: {e}")
        return jsonify({"error": "Callback handling failed"}), 500

@app.route('/finance')
def finance_callback():
    try:
        latest_finance = Finance.query.order_by(Finance.id.desc()).first()  

        if latest_finance:
            return jsonify({
                "id": latest_finance.id,
                "price": latest_finance.price,
            }), 200
        else:   
            return jsonify({"message": "No finance data found"}), 404
    except Exception as e:
        logging.error(f"Error handling finance callback: {e}")
        return jsonify({"error": "Callback handling failed"}), 500

@app.route('/')
def home():
    return 'Hello, World!'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
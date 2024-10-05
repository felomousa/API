import os
import time
import requests
from flask import Flask, jsonify, request, session, redirect, url_for
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # Use a secret key for session management

logging.basicConfig(level=logging.INFO)

# Spotify API credentials and scope
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = os.getenv("SPOTIFY_SCOPE")

# Function to retrieve Spotify client using OAuth tokens
def get_spotify_client():
    # Check if access token is available in session
    token_info = session.get('token_info', None)

    oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotipy_cache"
    )
    
    # If token is not cached or expired, retrieve new one
    if not token_info or oauth.is_token_expired(token_info):
        token_info = oauth.refresh_access_token(token_info['refresh_token']) if token_info else None
    
    # Store the updated token in the session
    session['token_info'] = token_info
    
    # Return Spotify client authenticated with the valid access token
    return spotipy.Spotify(auth=token_info['access_token'])

# Spotify OAuth callback route
@app.route('/callback')
def spotify_callback():
    try:
        oauth = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=".spotipy_cache"
        )

        # Get the authorization code from the URL
        code = request.args.get('code')
        
        # Exchange the code for access and refresh tokens
        token_info = oauth.get_access_token(code)

        # Store token information in the session securely
        session['token_info'] = token_info
        
        # Redirect user to the current-playing page or home
        return redirect(url_for('get_current_playing'))
    except Exception as e:
        logging.error(f"Callback error: {e}")
        return jsonify({"error": "Callback handling failed"}), 500

# Route to display the currently playing song
@app.route('/current-playing', methods=['GET'])
def get_current_playing():
    try:
        # Get the Spotify client
        spotify_client = get_spotify_client()
        
        # Get currently playing track information
        song_name, album_name, artist_name, album_cover_url, progress_ms, duration_ms = get_current_playing_info(spotify_client)
        
        if song_name is None:
            return jsonify({"message": "No track currently playing"}), 404
        
        return jsonify({
            "song_name": song_name,
            "album_name": album_name,
            "artist_name": artist_name,
            "album_cover_url": album_cover_url,
            "progress_ms": progress_ms,
            "duration_ms": duration_ms
        }), 200
    except Exception as e:
        logging.error(f"Error fetching current playing info: {e}")
        return jsonify({"error": "Unable to fetch current playing info"}), 500


def get_current_playing_info(spotify_client):
    try:
        # Call the Spotify API to get the currently playing track
        current_track = spotify_client.current_user_playing_track()
        
        # Log the full response from the API for debugging
        print("Current track response:", current_track)  # or use logging
        
        # Check if there is no currently playing track (current_track is None)
        if current_track is None or 'item' not in current_track:
            return None, None, None, None, None, None

        # Extract relevant information from the track data
        song_name = current_track['item']['name']
        album_name = current_track['item']['album']['name']
        artist_name = ", ".join([artist['name'] for artist in current_track['item']['artists']])
        album_cover_url = current_track['item']['album']['images'][0]['url']
        progress_ms = current_track['progress_ms']
        duration_ms = current_track['item']['duration_ms']

        return song_name, album_name, artist_name, album_cover_url, progress_ms, duration_ms

    except Exception as e:
        logging.error(f"Error fetching current playing info: {e}")
        return None, None, None, None, None, None




# Simple home route
@app.route('/')
def home():
    return 'Hello, World!'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

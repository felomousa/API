import os
import time
import requests
import numpy as np
from spotipy.oauth2 import SpotifyOAuth
import spotipy

def get_spotify_client():
    oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotipy_cache"
    )
    
    if not os.path.isfile(".spotipy_cache"):
        auth_url = oauth.get_authorize_url()
        print(f"Please navigate here in your browser: {auth_url}")
        response = input("Enter the URL you were redirected to: ")
        code = oauth.parse_response_code(response)
        token_info = oauth.get_access_token(code)
    else:
        token_info = oauth.get_cached_token()
    
    if not token_info:
        raise Exception("Authorization failed or token was not cached.")
    
    return spotipy.Spotify(auth=token_info['access_token'])

def get_current_playing_info(spotify_client):
    current_track = spotify_client.current_user_playing_track()
    if current_track is None:
        return None, None, None, None, None, None
    song_name = current_track['item']['name']
    album_name = current_track['item']['album']['name']
    artist_name = ", ".join([artist['name'] for artist in current_track['item']['artists']])
    album_cover_url = current_track['item']['album']['images'][0]['url']
    progress_ms = current_track['progress_ms']
    duration_ms = current_track['item']['duration_ms']
    return song_name, album_name, artist_name, album_cover_url, progress_ms, duration_ms
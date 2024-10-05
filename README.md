# Felo's API

A simple API providing my latest financial data, Netflix information, and Spotify activity.

## Endpoints

### `/finance`

**Description:**  
Retrieves the last reported All-Time value (%) of my stock portfolio. 

**Response:**
```json
{
  "id": 15,
  "value": 2.64
}
```

### `/netflix`

**Description:**  
Fetches information about the last watched movie & it's rating.

**Response:**
```json
{
  "poster_url": "https://s.ltrbxd.com/static/img/empty-poster-35.ed15236b.png",
  "rating": "★★★★½",
  "title": "Kingsman: The Secret Service"
}
```

### `/spotify`

**Description:**  
Provides details about the most recently played Spotify song.

**Response:**
```json
{
  "album_cover_url": "https://i.scdn.co/image/ab67616d0000b27376016873b8c84a5ee37d34d6",
  "album_name": "Sugarbread",
  "artist_name": "Soap&Skin",
  "song_name": "Me and the Devil",
  "time_played": "Sat, 05 Oct 2024 06:47:42 GMT"
}
```

## Usage

Access the endpoints using `curl` or any HTTP client:

- `https://callback.felomousa.com/finance`
- `https://callback.felomousa.com/netflix`
- `https://callback.felomousa.com/spotify`

## License

This project is licensed under the [MIT License](LICENSE)

import requests
import os

# Use your own TMDB API Key
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "87bd497a4e283cedf2bed0fd1a3e326e")  # fallback if env var not set

def get_movie_details(tmdb_id):
    """
    Fetches poster URL, IMDb rating, and tagline using TMDb API.
    """
    base_url = "https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US"
    url = base_url.format(tmdb_id, TMDB_API_KEY)

    try:
        response = requests.get(url)
        data = response.json()

        # Construct image URL and extract rating & tagline
        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
        rating = data.get('vote_average', 'N/A')
        tagline = data.get('tagline', '')

        return poster_url, rating, tagline
    except Exception as e:
        print(f"TMDb fetch error: {e}")
        return "", "N/A", ""

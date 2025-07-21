import requests
import os
from dotenv import load_dotenv # Add this line

# Load environment variables from .env file
load_dotenv() # Add this line

# Use your own TMDB API Key
TMDB_API_KEY = os.getenv("TMDB_API_KEY") # No fallback needed if you ensure it's in .env

def get_movie_details(tmdb_id):
    """
    Fetches poster URL, IMDb rating, and tagline using TMDb API.
    """
    if not TMDB_API_KEY:
        print("TMDB_API_KEY is not set. Please set it as an environment variable.")
        return "", "N/A", ""

    base_url = "https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US"
    url = base_url.format(tmdb_id, TMDB_API_KEY)

    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        # Construct image URL and extract rating & tagline
        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
        rating = data.get('vote_average', 'N/A')
        tagline = data.get('tagline', '')

        return poster_url, rating, tagline
    except requests.exceptions.RequestException as e:
        print(f"TMDb API request error: {e}")
        return "", "N/A", ""
    except ValueError as e: # For json decoding errors
        print(f"TMDb API JSON decoding error: {e}")
        return "", "N/A", ""
    except Exception as e:
        print(f"An unexpected error occurred in TMDb fetch: {e}")
        return "", "N/A", ""

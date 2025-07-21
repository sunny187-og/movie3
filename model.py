# model.py

import pandas as pd
import numpy as np
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# These will be set in load_data()
movies = None
cos_sim = None
title_to_index = None
title_to_tmdb_id = None

# Modified extract_names to return a list or string
def extract_names(json_str, key='name', topn=None, as_list=False):
    """
    Extracts names from a JSON string (like 'genres', 'cast', 'keywords').
    Can return names as a list or a space-separated string.
    """
    try:
        items = ast.literal_eval(json_str)
        names = [item[key] for item in items]
        if as_list:
            return names[:topn] if topn else names
        else:
            return ' '.join(names[:topn]) if topn else ' '.join(names)
    except (ValueError, SyntaxError, TypeError): # Added TypeError for robustness
        return [] if as_list else ''

def get_director(crew_str):
    """
    Extracts the director's name from the 'crew' JSON string.
    """
    try:
        crew = ast.literal_eval(crew_str)
        for member in crew:
            if member.get('job') == 'Director':
                return member.get('name', '')
        return ''
    except (ValueError, SyntaxError, TypeError): # Added TypeError for robustness
        return ''

def load_data():
    """
    Loads, merges, and preprocesses movie data for the recommender.
    Initializes global 'movies' DataFrame, cosine similarity matrix, and mappings.
    """
    global movies, cos_sim, title_to_index, title_to_tmdb_id

    # Load data
    try:
        metadata = pd.read_csv("data/clean_metadata.csv")
        credits = pd.read_csv("data/trimmed_credits.csv")
        keywords = pd.read_csv("data/clean_keywords.csv")
    except FileNotFoundError as e:
        print(f"Error loading data files: {e}. Make sure 'data/' directory contains the CSVs.")
        # Create empty DataFrames to avoid further errors
        movies = pd.DataFrame()
        cos_sim = np.array([[]])
        title_to_index = pd.Series()
        title_to_tmdb_id = pd.Series()
        return

    # Merge DataFrames on 'id'
    movies = metadata.merge(credits, on='id').merge(keywords, on='id')

    # Convert 'id' to numeric, coerce errors to NaN and drop them
    # This is important if some IDs are not valid numbers
    movies['id'] = pd.to_numeric(movies['id'], errors='coerce')
    movies.dropna(subset=['id'], inplace=True)
    movies['id'] = movies['id'].astype(int)

    # Process 'genres' and 'keywords' for soup (as space-separated strings)
    movies['genres'] = movies['genres'].apply(extract_names, as_list=False)
    movies['keywords'] = movies['keywords'].apply(extract_names, as_list=False)

    # Process 'cast' for top actors
    # 'top_actors_list' stores actual names as a list for get_all_actors() and details display
    movies['top_actors_list'] = movies['cast'].apply(lambda x: extract_names(x, topn=3, as_list=True))
    # 'top_actors_soup' stores names as a space-separated string for TF-IDF soup
    movies['top_actors_soup'] = movies['top_actors_list'].apply(lambda x: ' '.join(x))

    # Process 'crew' for director
    movies['director'] = movies['crew'].apply(get_director)

    # Create the 'soup' column for TF-IDF vectorization
    def create_soup(row):
        return f"{row['genres']} {row['keywords']} {row['top_actors_soup']} {row['director']}"

    movies['soup'] = movies.apply(create_soup, axis=1)

    # TF-IDF Vectorization and Cosine Similarity
    tfidf = TfidfVectorizer(stop_words='english')
    # Fill NaN values in 'soup' before fitting to prevent errors
    soup_matrix = tfidf.fit_transform(movies['soup'].fillna(''))
    cos_sim = cosine_similarity(soup_matrix, soup_matrix)

    # Prepare final 'movies' DataFrame for recommendations and lookups
    # Renamed 'id' to 'tmdb_id' for clarity
    movies = movies[['id', 'title', 'soup', 'genres', 'director', 'top_actors_list']].rename(columns={'id': 'tmdb_id'})
    movies.reset_index(drop=True, inplace=True)

    # Create mappings for quick lookups
    title_to_index = pd.Series(movies.index, index=movies['title'])
    title_to_tmdb_id = pd.Series(movies['tmdb_id'].values, index=movies['title'])

def get_recommendations(fav_movie, actor=None, director=None, genre=None, mood=None, topn=5):
    """
    Generates movie recommendations based on a favorite movie and optional preferences.
    """
    if movies is None or fav_movie not in title_to_index:
        return [] # Return empty list if data not loaded or movie not found

    idx = title_to_index[fav_movie]

    # Get cosine similarity scores, converting tolist() to prevent ValueError
    sim_scores = list(enumerate(cos_sim[idx].tolist()))

    # Sort by similarity score in descending order
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get top similar movies (excluding the input movie itself)
    # Using a wider pool for boosting before final selection
    sim_scores = sim_scores[1:50]
    movie_indices = [i[0] for i in sim_scores]
    candidates = movies.iloc[movie_indices].copy()

    def calculate_boost_score(row):
        score = 0
        reason = []

        # Boost by Actor (check if selected actor is in the movie's top_actors_list)
        if actor and actor in row['top_actors_list']:
            score += 0.5
            reason.append(f"Features {actor}")
        # Boost by Director (case-insensitive exact match)
        if director and row['director'] and director.lower() == row['director'].lower():
            score += 0.5
            reason.append(f"Directed by {director}")
        # Boost by Genre (check if selected genre is in the movie's genres string)
        if genre and row['genres'] and genre.lower() in row['genres'].lower():
            score += 0.3
            reason.append(f"Is a {genre} movie")

        # Boost by Mood (check for related genres based on mood)
        if mood:
            mood_genre_map = {
                'happy': ['comedy', 'adventure', 'family'],
                'sad': ['drama', 'romance'],
                'excited': ['action', 'sci-fi', 'adventure'],
                'romantic': ['romance', 'drama'],
                'curious': ['mystery', 'documentary'],
                'dark': ['thriller', 'horror', 'crime'],
                'calm': ['documentary', 'drama', 'history']
            }
            related_genres = mood_genre_map.get(mood.lower(), [])
            if related_genres and row['genres']:
                if any(g.lower() in row['genres'].lower() for g in related_genres):
                    score += 0.3
                    reason.append(f"Matches your '{mood}' mood")
        return score, "; ".join(reason) if reason else "Similar to your favorite movie"

    # Apply boosting to candidate movies
    candidates[['boost', 'reason']] = candidates.apply(lambda row: pd.Series(calculate_boost_score(row)), axis=1)
    candidates['final_score'] = candidates['boost'] + candidates.index.map(lambda x: cos_sim[idx][x])

    # Sort by final score and get top recommendations
    final_recommendations = candidates.sort_values('final_score', ascending=False)

    # Return a list of dictionaries with required details
    return final_recommendations.head(topn).apply(
        lambda row: {'title': row['title'], 'tmdb_id': row['tmdb_id'], 'reason': row['reason']}, axis=1
    ).tolist()

# Helper function to get movie details from the local DataFrame for display
def get_movie_details_from_df(movie_title):
    """
    Fetches movie details (genres, director, top_actors_list) from the local 'movies' DataFrame.
    """
    if movies is not None and movie_title in movies['title'].values:
        movie_row = movies[movies['title'] == movie_title].iloc[0]
        return {
            'genres': movie_row['genres'], # This is the space-separated string
            'director': movie_row['director'],
            'top_actors': movie_row['top_actors_list'] # This is the list of actors
        }
    return {'genres': 'N/A', 'director': 'N/A', 'top_actors': []}


# --- Helper functions for Streamlit Selectboxes ---
def get_all_movies():
    """Returns a dictionary mapping movie titles to TMDB IDs."""
    if movies is not None:
        return title_to_tmdb_id.to_dict()
    return {}

def get_all_actors():
    """Returns a sorted list of unique top actor names."""
    if movies is not None:
        all_actors = set()
        # Iterate through lists of actors for each movie
        for actors_list_for_movie in movies['top_actors_list'].dropna():
            for actor_name in actors_list_for_movie:
                if actor_name: # Ensure it's not an empty string
                    all_actors.add(actor_name.strip())
        return sorted(list(all_actors))
    return []

def get_all_directors():
    """Returns a sorted list of unique director names."""
    if movies is not None:
        # Filter out empty strings/NaNs before getting unique values
        return sorted(movies['director'].dropna().astype(str).unique().tolist())
    return []

def get_all_genres():
    """Returns a sorted list of unique genre names."""
    if movies is not None:
        genre_list = set()
        # Iterate through space-separated genre strings
        for genres_str in movies['genres'].dropna():
            for genre_name in genres_str.split(' '):
                if genre_name:
                    genre_list.add(genre_name.strip())
        return sorted(list(genre_list))
    return []

# Load data on module import
load_data()

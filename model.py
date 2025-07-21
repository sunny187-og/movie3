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
# Add a global variable for title to tmdb_id mapping
title_to_tmdb_id = None

def extract_names(json_str, key='name', topn=None):
    try:
        items = ast.literal_eval(json_str)
        names = [item[key] for item in items]
        return ' '.join(names[:topn]) if topn else ' '.join(names)
    except (ValueError, SyntaxError): # Catch more potential parsing errors
        return ''

def get_director(crew_str):
    try:
        crew = ast.literal_eval(crew_str)
        for member in crew:
            if member.get('job') == 'Director':
                return member.get('name', '')
        return ''
    except (ValueError, SyntaxError): # Catch more potential parsing errors
        return ''

def load_data():
    global movies, cos_sim, title_to_index, title_to_tmdb_id

    metadata = pd.read_csv("data/clean_metadata.csv")
    credits = pd.read_csv("data/trimmed_credits.csv")
    keywords = pd.read_csv("data/clean_keywords.csv")

    movies = metadata.merge(credits, on='id').merge(keywords, on='id')
    movies['genres'] = movies['genres'].apply(extract_names)
    movies['keywords'] = movies['keywords'].apply(extract_names)
    movies['top_actors'] = movies['cast'].apply(lambda x: extract_names(x, topn=3))
    movies['director'] = movies['crew'].apply(get_director)

    def create_soup(row):
        return f"{row['genres']} {row['keywords']} {row['top_actors']} {row['director']}"

    movies['soup'] = movies.apply(create_soup, axis=1)

    tfidf = TfidfVectorizer(stop_words='english')
    # Handle NaN values in 'soup' column before fitting
    soup_matrix = tfidf.fit_transform(movies['soup'].fillna(''))
    cos_sim = cosine_similarity(soup_matrix, soup_matrix)

    # Make sure 'id' column is the TMDB ID, rename it to tmdb_id for clarity
    movies = movies[['id', 'title', 'soup', 'genres', 'director', 'top_actors']].rename(columns={'id': 'tmdb_id'})
    movies.reset_index(drop=True, inplace=True)
    title_to_index = pd.Series(movies.index, index=movies['title'])
    # Create the new mapping from title to tmdb_id
    title_to_tmdb_id = pd.Series(movies['tmdb_id'].values, index=movies['title'])

    return movies

def get_recommendations(fav_movie, actor=None, director=None, genre=None, mood=None, topn=5):
    if fav_movie not in title_to_index:
        return [] # Return an empty list if movie not found, as app.py expects a list

    # Step 1: Get index of the favorite movie
    idx = title_to_index[fav_movie]

    # Step 2: Get cosine similarity scores
    sim_scores = list(enumerate(cos_sim[idx]))

    # Step 3: Sort by similarity score
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Step 4: Get top similar movies (excluding the input movie itself)
    sim_scores = sim_scores[1:50]  # wider pool for boosting
    movie_indices = [i[0] for i in sim_scores]

    # Step 5: Prepare candidate movies
    candidates = movies.iloc[movie_indices].copy()

    def calculate_boost_score(row):
        score = 0
        reason = [] # To store why a movie was recommended

        if actor and actor.lower() in row['top_actors'].lower(): # Check top_actors for actor
            score += 0.5
            reason.append(f"Features {actor}")
        if director and director.lower() in row['director'].lower(): # Check director column for director
            score += 0.5
            reason.append(f"Directed by {director}")
        if genre and genre.lower() in row['genres'].lower(): # Check genres column for genre
            score += 0.3
            reason.append(f"Is a {genre} movie")

        if mood:
            mood_genre_map = {
                'happy': ['comedy', 'adventure', 'family'],
                'sad': ['drama', 'romance'],
                'excited': ['action', 'sci-fi', 'adventure'], # Added 'adventure' for 'excited'
                'romantic': ['romance', 'drama'], # Added 'romantic' mood mapping
                'curious': ['mystery', 'documentary'], # Added 'curious' mood mapping
                'dark': ['thriller', 'horror', 'crime'], # Added 'dark' mood mapping
                'calm': ['documentary', 'drama', 'history'] # Added 'calm' mood mapping
            }
            related_genres = mood_genre_map.get(mood.lower(), [])
            if any(g.lower() in row['genres'].lower() for g in related_genres): # Check genres for mood
                score += 0.3
                reason.append(f"Matches your '{mood}' mood")
        return score, "; ".join(reason) if reason else "Similar to your favorite movie"

    candidates[['boost', 'reason']] = candidates.apply(lambda row: pd.Series(calculate_boost_score(row)), axis=1)
    candidates['final_score'] = candidates['boost'] + candidates.index.map(lambda x: cos_sim[idx][x])
    final_recommendations = candidates.sort_values('final_score', ascending=False)

    # Return a list of dictionaries as app.py expects
    return final_recommendations.head(topn).apply(
        lambda row: {'title': row['title'], 'tmdb_id': row['tmdb_id'], 'reason': row['reason']}, axis=1
    ).tolist()


# Aliases and helper functions expected by app.py
recommend = get_recommendations  # Alias for import

def get_all_movies():
    # Return a dictionary mapping title to tmdb_id
    if movies is not None:
        return title_to_tmdb_id.to_dict()
    return {}

def get_all_actors():
    # Collect all unique actors from 'top_actors' column
    if movies is not None:
        all_actors = set()
        for actors_str in movies['top_actors'].dropna():
            for actor in actors_str.split(' '): # Split by space as per extract_names
                if actor: # Ensure not empty string
                    all_actors.add(actor.strip())
        return sorted(list(all_actors))
    return []

def get_all_directors():
    # Collect all unique directors from 'director' column
    if movies is not None:
        return sorted(movies['director'].dropna().unique().tolist())
    return []

def get_all_genres():
    if movies is not None:
        genre_list = set()
        for genres_str in movies['genres'].dropna():
            # Genres are space-separated strings after extract_names
            for genre in genres_str.split(' '):
                if genre: # Ensure not empty string
                    genre_list.add(genre.strip())
        return sorted(list(genre_list))
    return []

# Load data on module import
load_data()

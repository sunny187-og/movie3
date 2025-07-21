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

# Modified extract_names to return a list
def extract_names(json_str, key='name', topn=None, as_list=False):
    try:
        items = ast.literal_eval(json_str)
        names = [item[key] for item in items]
        if as_list:
            return names[:topn] if topn else names
        else:
            return ' '.join(names[:topn]) if topn else ' '.join(names)
    except (ValueError, SyntaxError):
        return [] if as_list else '' # Return empty list if as_list is True


def get_director(crew_str):
    try:
        crew = ast.literal_eval(crew_str)
        for member in crew:
            if member.get('job') == 'Director':
                return member.get('name', '')
        return ''
    except (ValueError, SyntaxError):
        return ''

def load_data():
    global movies, cos_sim, title_to_index, title_to_tmdb_id

    metadata = pd.read_csv("data/clean_metadata.csv")
    credits = pd.read_csv("data/trimmed_credits.csv")
    keywords = pd.read_csv("data/clean_keywords.csv")

    movies = metadata.merge(credits, on='id').merge(keywords, on='id')
    movies['genres'] = movies['genres'].apply(extract_names, as_list=False) # Keep as string for soup
    movies['keywords'] = movies['keywords'].apply(extract_names, as_list=False) # Keep as string for soup

    # Store top actors as a list for get_all_actors()
    movies['top_actors_list'] = movies['cast'].apply(lambda x: extract_names(x, topn=3, as_list=True))
    # Use space-separated string for 'soup' column
    movies['top_actors_soup'] = movies['top_actors_list'].apply(lambda x: ' '.join(x))


    movies['director'] = movies['crew'].apply(get_director)

    def create_soup(row):
        # Use top_actors_soup for the soup
        return f"{row['genres']} {row['keywords']} {row['top_actors_soup']} {row['director']}"

    movies['soup'] = movies.apply(create_soup, axis=1)

    tfidf = TfidfVectorizer(stop_words='english')
    soup_matrix = tfidf.fit_transform(movies['soup'].fillna(''))
    cos_sim = cosine_similarity(soup_matrix, soup_matrix)

    # Include 'genres' (original string) and 'director' for boosting logic
    # Add 'top_actors_list' as well
    movies = movies[['id', 'title', 'soup', 'genres', 'director', 'top_actors_list']].rename(columns={'id': 'tmdb_id'})
    movies.reset_index(drop=True, inplace=True)
    title_to_index = pd.Series(movies.index, index=movies['title'])
    title_to_tmdb_id = pd.Series(movies['tmdb_id'].values, index=movies['title'])

    return movies

def get_recommendations(fav_movie, actor=None, director=None, genre=None, mood=None, topn=5):
    if fav_movie not in title_to_index:
        return []

    idx = title_to_index[fav_movie]
    sim_scores = list(enumerate(cos_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:50]
    movie_indices = [i[0] for i in sim_scores]
    candidates = movies.iloc[movie_indices].copy()

    def calculate_boost_score(row):
        score = 0
        reason = []

        # Check if actor is in the list of top actors for this movie
        if actor and actor in row['top_actors_list']:
            score += 0.5
            reason.append(f"Features {actor}")
        if director and director.lower() == row['director'].lower(): # Exact match for director
            score += 0.5
            reason.append(f"Directed by {director}")
        if genre and genre.lower() in row['genres'].lower():
            score += 0.3
            reason.append(f"Is a {genre} movie")

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
            if any(g.lower() in row['genres'].lower() for g in related_genres):
                score += 0.3
                reason.append(f"Matches your '{mood}' mood")
        return score, "; ".join(reason) if reason else "Similar to your favorite movie"

    candidates[['boost', 'reason']] = candidates.apply(lambda row: pd.Series(calculate_boost_score(row)), axis=1)
    candidates['final_score'] = candidates['boost'] + candidates.index.map(lambda x: cos_sim[idx][x])
    final_recommendations = candidates.sort_values('final_score', ascending=False)

    return final_recommendations.head(topn).apply(
        lambda row: {'title': row['title'], 'tmdb_id': row['tmdb_id'], 'reason': row['reason']}, axis=1
    ).tolist()


recommend = get_recommendations

def get_all_movies():
    if movies is not None:
        return title_to_tmdb_id.to_dict()
    return {}

def get_all_actors():
    # Now correctly extract unique full actor names from 'top_actors_list'
    if movies is not None:
        all_actors = set()
        for actors_list_for_movie in movies['top_actors_list'].dropna():
            for actor_name in actors_list_for_movie:
                if actor_name: # Ensure it's not an empty string
                    all_actors.add(actor_name.strip())
        return sorted(list(all_actors))
    return []

def get_all_directors():
    if movies is not None:
        # Filter out empty strings before getting unique values
        return sorted(movies['director'].dropna().astype(str).unique().tolist())
    return []

def get_all_genres():
    if movies is not None:
        genre_list = set()
        # 'genres' column is already a space-separated string from extract_names(as_list=False)
        for genres_str in movies['genres'].dropna():
            for genre_name in genres_str.split(' '):
                if genre_name:
                    genre_list.add(genre_name.strip())
        return sorted(list(genre_list))
    return []

# Load data on module import
load_data()

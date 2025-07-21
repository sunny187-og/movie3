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

def extract_names(json_str, key='name', topn=None):
    try:
        items = ast.literal_eval(json_str)
        names = [item[key] for item in items]
        return ' '.join(names[:topn]) if topn else ' '.join(names)
    except:
        return ''

def get_director(crew_str):
    try:
        crew = ast.literal_eval(crew_str)
        for member in crew:
            if member.get('job') == 'Director':
                return member.get('name', '')
        return ''
    except:
        return ''

def load_data():
    global movies, cos_sim, title_to_index

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
    soup_matrix = tfidf.fit_transform(movies['soup'].fillna(''))
    cos_sim = cosine_similarity(soup_matrix, soup_matrix)

    movies = movies[['id', 'title', 'soup']].rename(columns={'id': 'movieId'})
    movies.reset_index(drop=True, inplace=True)
    title_to_index = pd.Series(movies.index, index=movies['title'])

    return movies

def get_recommendations(fav_movie, actor=None, director=None, genre=None, mood=None, topn=5):
    if fav_movie not in title_to_index:
        return f"'{fav_movie}' not found in dataset."

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

    def boost(row):
        score = 0
        if actor and actor.lower() in row['soup'].lower():
            score += 0.5
        if director and director.lower() in row['soup'].lower():
            score += 0.5
        if genre and genre.lower() in row['soup'].lower():
            score += 0.3
        if mood:
            mood_genre_map = {
                'happy': ['comedy', 'adventure', 'family'],
                'sad': ['drama', 'romance'],
                'thrilling': ['thriller', 'mystery', 'action'],
                'scary': ['horror', 'mystery'],
                'exciting': ['action', 'sci-fi'],
                'emotional': ['drama', 'romance']
            }
            related_genres = mood_genre_map.get(mood.lower(), [])
            if any(g.lower() in row['soup'].lower() for g in related_genres):
                score += 0.3
        return score

    candidates['boost'] = candidates.apply(boost, axis=1)
    candidates['final_score'] = candidates['boost'] + candidates.index.map(lambda x: cos_sim[idx][x])
    final_recommendations = candidates.sort_values('final_score', ascending=False)
    return final_recommendations['title'].head(topn).tolist()


# Aliases and helper functions expected by app.py
recommend = get_recommendations  # Alias for import

def get_all_movies():
    return movies['title'].tolist()

def get_all_actors():
    return sorted(set(actor for soup in movies['soup'] for actor in soup.split() if actor.istitle()))

def get_all_directors():
    return sorted(set(movies['soup'].str.extract(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)')[0].dropna()))

def get_all_genres():
    all_genres = set()
    for genre_list in movies['genres']:
        for genre in genre_list.split():
            all_genres.add(genre.strip())
    return sorted(all_genres)



import streamlit as st
import random
from model import recommend, get_all_movies, get_all_actors, get_all_directors, get_all_genres
from utils import get_movie_details

st.set_page_config(page_title="Movie Recommender", layout="wide")

# ----------------- Session Init -----------------
if "favorite" not in st.session_state:
    st.session_state.favorite = None

# ----------------- Header -----------------
st.title("🎬 Movie Recommender")

# ----------------- Favorite Movie Search -----------------
all_movies = get_all_movies()
fav_movie_input = st.text_input("Search for your favorite movie", key="fav_input")

if fav_movie_input:
    filtered = [m for m in all_movies if fav_movie_input.lower() in m.lower()]
    top10 = filtered[:10]
    for i, movie in enumerate(top10):
        if st.button(movie, key=f"movie_btn_{i}"):
            st.session_state.favorite = movie

# ----------------- Favorite Movie Thumbnail -----------------
if st.session_state.favorite:
    st.markdown(f"**Selected Favorite:** {st.session_state.favorite}")
    tmdb_id = all_movies.get(st.session_state.favorite)
    if tmdb_id:
        poster_url, _, _ = get_movie_details(tmdb_id)
        if poster_url:
            st.image(poster_url, width=150)

# ----------------- Popular Movies Scroll Section -----------------
st.markdown("#### Or pick from popular movies")
popular_movies = random.sample(list(all_movies.items()), min(30, len(all_movies)))
pages = [popular_movies[i:i+10] for i in range(0, len(popular_movies), 10)]

if "page" not in st.session_state:
    st.session_state.page = 0

cols = st.columns([1, 10, 1])
with cols[0]:
    if st.button("⬅️", key="prev"):
        st.session_state.page = max(0, st.session_state.page - 1)

with cols[2]:
    if st.button("➡️", key="next"):
        st.session_state.page = min(len(pages) - 1, st.session_state.page + 1)

# Display grid of 2 rows x 5 columns
with cols[1]:
    grid = pages[st.session_state.page]
    for row in range(2):
        cols_row = st.columns(5)
        for col in range(5):
            idx = row * 5 + col
            if idx < len(grid):
                name, tmdb_id = grid[idx]
                poster_url, _, _ = get_movie_details(tmdb_id)
                if poster_url:
                    if cols_row[col].button("", key=f"pop_{name}"):
                        st.session_state.favorite = name
                    cols_row[col].image(poster_url, caption=name, use_column_width=True)

# ----------------- Additional Preferences -----------------
st.markdown("### Additional Preferences")

actor = st.selectbox("🎭 Favorite Actor", [""] + get_all_actors())
director = st.selectbox("🎬 Favorite Director", [""] + get_all_directors())
genre = st.selectbox("🎞️ Favorite Genre", [""] + get_all_genres())
mood = st.selectbox("🧠 Your Mood", ["", "Happy", "Sad", "Excited", "Romantic", "Curious", "Dark", "Calm"])

# ----------------- Recommendation -----------------
if st.button("Recommend Movies 🎯"):
    if not st.session_state.favorite:
        st.warning("Please select a favorite movie first.")
    else:
        st.subheader("🎉 Recommended for You:")
        recommendations = recommend(
            fav_movie=st.session_state.favorite,
            actor=actor,
            director=director,
            genre=genre,
            mood=mood
        )

        for rec in recommendations:
            title = rec['title']
            tmdb_id = rec['tmdb_id']
            reason = rec['reason']
            poster_url, rating, tagline = get_movie_details(tmdb_id)

            cols = st.columns([1, 4])
            with cols[0]:
                if poster_url:
                    st.image(poster_url, width=100)
            with cols[1]:
                st.markdown(f"**{title}**")
                st.markdown(f"⭐ IMDb: {rating if rating else 'N/A'}")
                st.markdown(f"📝 {tagline if tagline else reason}")
                st.markdown("---")

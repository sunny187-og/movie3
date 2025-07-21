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
all_movies = get_all_movies() # This is now a dictionary: {title: tmdb_id}
fav_movie_input = st.text_input("Search for your favorite movie", key="fav_input")

if fav_movie_input:
    # Filter movie titles based on input (case-insensitive)
    filtered_titles = [m_title for m_title in all_movies.keys() if fav_movie_input.lower() in m_title.lower()]
    top10 = filtered_titles[:10]
    for i, movie_title in enumerate(top10):
        # Use a distinct key for each button to avoid conflicts
        if st.button(movie_title, key=f"fav_search_btn_{i}"):
            st.session_state.favorite = movie_title

# ----------------- Favorite Movie Thumbnail -----------------
if st.session_state.favorite:
    st.markdown(f"**Selected Favorite:** {st.session_state.favorite}")
    # Retrieve tmdb_id using the selected movie title from the dictionary
    tmdb_id = all_movies.get(st.session_state.favorite)
    if tmdb_id:
        poster_url, _, _ = get_movie_details(tmdb_id)
        if poster_url:
            st.image(poster_url, width=150)

# ----------------- Popular Movies Scroll Section -----------------
st.markdown("#### Or pick from popular movies")
# Get a list of (title, tmdb_id) tuples from all_movies dictionary
all_movie_items = list(all_movies.items())
# Ensure there are enough movies to sample, otherwise take all
num_samples = min(30, len(all_movie_items))
popular_movies = random.sample(all_movie_items, num_samples)
pages = [popular_movies[i:i+10] for i in range(0, len(popular_movies), 10)]

if "page" not in st.session_state:
    st.session_state.page = 0

cols = st.columns([1, 10, 1])
with cols[0]:
    if st.button("⬅️", key="prev_page"): # Changed key to avoid conflict
        st.session_state.page = max(0, st.session_state.page - 1)

with cols[2]:
    if st.button("➡️", key="next_page"): # Changed key to avoid conflict
        st.session_state.page = min(len(pages) - 1, st.session_state.page + 1)

# Display grid of 2 rows x 5 columns
with cols[1]:
    grid = pages[st.session_state.page]
    for row_idx in range(2): # Use row_idx to avoid conflict with 'row' var
        cols_row = st.columns(5)
        for col_idx in range(5): # Use col_idx to avoid conflict with 'col' var
            idx = row_idx * 5 + col_idx
            if idx < len(grid):
                name, tmdb_id = grid[idx] # 'name' here is the movie title
                poster_url, _, _ = get_movie_details(tmdb_id)

                with cols_row[col_idx]: # Place elements within the specific column
                    if poster_url:
                        st.image(poster_url, caption=name, use_container_width=True)
                    else:
                        st.write(name) # Display name if poster not available

                    # Add an explicit button for selection below the image
                    if st.button("Select", key=f"pop_select_{name}_{tmdb_id}"): # Unique key combining name and tmdb_id
                        st.session_state.favorite = name
                        st.rerun() # Rerun to immediately update the favorite movie thumbnail

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

        if not recommendations: # Handle case where no recommendations are found
            st.info("No recommendations found based on your criteria. Try different preferences!")
        else:
            for rec in recommendations:
                title = rec['title']
                tmdb_id = rec['tmdb_id']
                reason = rec['reason']
                poster_url, rating, tagline = get_movie_details(tmdb_id)

                cols_rec = st.columns([1, 4]) # Changed variable name to avoid conflict
                with cols_rec[0]:
                    if poster_url:
                        st.image(poster_url, width=100)
                with cols_rec[1]:
                    st.markdown(f"**{title}**")
                    st.markdown(f"⭐ IMDb: {rating if rating else 'N/A'}")
                    st.markdown(f"📝 {tagline if tagline else reason}")
                    st.markdown("---")

import streamlit as st
import random
from model import recommend, get_all_movies, get_all_actors, get_all_directors, get_all_genres
from utils import get_movie_details

st.set_page_config(page_title="Movie Recommender", layout="wide")

# ----------------- Session Init -----------------
if "favorite" not in st.session_state:
    st.session_state.favorite = None
if "page" not in st.session_state:
    st.session_state.page = 0
# Initialize popular_movies and pages ONLY ONCE
if "popular_movies_data" not in st.session_state:
    all_movies_items = list(get_all_movies().items())
    num_samples = min(30, len(all_movies_items))
    st.session_state.popular_movies_data = random.sample(all_movies_items, num_samples)
    st.session_state.popular_movies_pages = [st.session_state.popular_movies_data[i:i+10] for i in range(0, len(st.session_state.popular_movies_data), 10)]


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
            st.rerun() # Added rerun for immediate feedback

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

# Use the cached data from session state
pages = st.session_state.popular_movies_pages

cols = st.columns([1, 10, 1])
with cols[0]:
    if st.button("⬅️", key="prev_page"):
        st.session_state.page = max(0, st.session_state.page - 1)
        st.rerun() # Rerun to update the page display

with cols[2]:
    if st.button("➡️", key="next_page"):
        st.session_state.page = min(len(pages) - 1, st.session_state.page + 1)
        st.rerun() # Rerun to update the page display

# Display grid of 2 rows x 5 columns
with cols[1]:
    # Ensure current page is valid after potential resets or changes
    current_page_idx = st.session_state.page
    if not (0 <= current_page_idx < len(pages)):
        current_page_idx = 0 # Reset to first page if out of bounds
        st.session_state.page = 0

    grid = pages[current_page_idx]
    for row_idx in range(2):
        cols_row = st.columns(5)
        for col_idx in range(5):
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
                        # We do NOT want to change st.session_state.page here.
                        # st.rerun() will simply re-render the app with the NEW favorite.
                        st.rerun()

# ----------------- Additional Preferences -----------------
st.markdown("### Additional Preferences")

# Ensure the selectbox options are fetched on each rerun
actor_options = [""] + get_all_actors()
director_options = [""] + get_all_directors()
genre_options = [""] + get_all_genres()

actor = st.selectbox("🎭 Favorite Actor", actor_options, key="actor_select")
director = st.selectbox("🎬 Favorite Director", director_options, key="director_select")
genre = st.selectbox("🎞️ Favorite Genre", genre_options, key="genre_select")
mood = st.selectbox("🧠 Your Mood", ["", "Happy", "Sad", "Excited", "Romantic", "Curious", "Dark", "Calm"], key="mood_select")


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

                cols_rec = st.columns([1, 4])
                with cols_rec[0]:
                    if poster_url:
                        st.image(poster_url, width=100)
                with cols_rec[1]:
                    st.markdown(f"**{title}**")
                    st.markdown(f"⭐ IMDb: {rating if rating else 'N/A'}")
                    st.markdown(f"📝 {tagline if tagline else reason}")
                    st.markdown("---")

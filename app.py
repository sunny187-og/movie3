import streamlit as st
import random
# Ensure model.py is correctly updated with all previous fixes
from model import recommend, get_all_movies, get_all_actors, get_all_directors, get_all_genres, get_movie_details_from_df
from utils import get_movie_details as get_movie_details_tmdb # Renamed to avoid clash with local function

st.set_page_config(page_title="Movie Recommender", layout="wide")

# ----------------- Session State Initialization -----------------
if "favorite" not in st.session_state:
    st.session_state.favorite = None
if "page" not in st.session_state:
    st.session_state.page = 0
# Initialize and cache popular_movies data and pages ONLY ONCE
if "popular_movies_data" not in st.session_state:
    all_movies_items = list(get_all_movies().items())
    num_samples = min(30, len(all_movies_items))
    st.session_state.popular_movies_data = random.sample(all_movies_items, num_samples)
    st.session_state.popular_movies_pages = [st.session_state.popular_movies_data[i:i+10] for i in range(0, len(st.session_state.popular_movies_data), 10)]
# Initialize search results if not present
if "search_results_display" not in st.session_state:
    st.session_state.search_results_display = []

# --- No more get_movie_card_html_simplified helper function ---
# It's removed because it was causing the persistent HTML rendering issues.

# ----------------- Header -----------------
st.title("🎬 Movie Recommender")

# ----------------- Favorite Movie Search Input -----------------
all_movies = get_all_movies()
fav_movie_input = st.text_input("Search for your favorite movie", key="fav_input")

if fav_movie_input:
    filtered_titles = [m_title for m_title in all_movies.keys() if fav_movie_input.lower() in m_title.lower()]
    st.session_state.search_results_display = filtered_titles[:10]

    if st.session_state.search_results_display:
        st.markdown("#### Search Results:")
        search_grid_layout = st.columns(5)

        for i in range(10):
            with search_grid_layout[i % 5]:
                if i < len(st.session_state.search_results_display):
                    name = st.session_state.search_results_display[i]
                    tmdb_id = all_movies.get(name)

                    poster_url, rating, _ = "", "N/A", ""
                    if tmdb_id:
                        poster_url, rating, _ = get_movie_details_tmdb(tmdb_id)

                    # --- Native Streamlit display for search results ---
                    if poster_url:
                        st.image(poster_url, use_column_width=True)
                    else:
                        st.markdown('<div style="background-color:#333; height:150px; display:flex; align-items:center; justify-content:center; border-radius:5px; color:#bbb; text-align:center; font-size:0.9em;">No Poster Available</div>', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True) # Add some space if no poster

                    st.markdown(f"**⭐ {rating if rating != 'N/A' else 'N/A'}**")
                    st.markdown(f"**{name}**")

                    if st.button("Select", key=f"search_select_{name}_{tmdb_id}"):
                        st.session_state.favorite = name
                        st.rerun()
                else:
                    # Empty slots for alignment
                    st.markdown(
                        '''
                        <div style="width: 100%; height: 150px; background-color: #222; display: flex;
                                    align-items: center; justify-content: center; border-radius: 5px;
                                    color: #555; font-size: 0.9em;">
                            &nbsp;
                        </div>
                        <div style="font-size: 0.9em; margin-top: 5px; text-align: center; color: #555;">&nbsp;</div>
                        <div style="height: 38px;">&nbsp;</div>
                        ''', unsafe_allow_html=True
                    )
    else:
        st.info("No movies found matching your search. Try a different query!")
else:
    st.session_state.search_results_display = []

# ----------------- Favorite Movie Thumbnail and Details -----------------
if st.session_state.favorite:
    st.markdown(f"**Selected Favorite:** {st.session_state.favorite}")
    tmdb_id = all_movies.get(st.session_state.favorite)

    if tmdb_id:
        poster_url, rating, tagline = get_movie_details_tmdb(tmdb_id)
        local_details = get_movie_details_from_df(st.session_state.favorite)

        fav_cols = st.columns([1, 4])

        with fav_cols[0]:
            # --- Native Streamlit display for favorite movie ---
            if poster_url:
                st.image(poster_url, width=150)
            else:
                st.markdown('<div style="width:150px; height:225px; background-color:#333; display:flex; align-items:center; justify-content:center; border-radius:5px; color:#bbb; text-align:center; font-size:1em; font-weight:bold;">No Poster Available</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True) # Add some space

            st.markdown(f"**⭐ {rating if rating != 'N/A' else 'N/A'}**")


        with fav_cols[1]:
            if tagline:
                st.markdown(f"📝 *{tagline}*")
            else:
                st.markdown(f"📝 *No tagline available.*")

            if local_details and local_details['top_actors']:
                actors_display = ", ".join(local_details['top_actors'])
                st.markdown(f"**🎭 Actors:** {actors_display}")
            else:
                st.markdown("**🎭 Actors:** N/A")

            if local_details and local_details['director']:
                st.markdown(f"**🎬 Director:** {local_details['director']}")
            else:
                st.markdown("**🎬 Director:** N/A")

            if local_details and local_details['genres']:
                st.markdown(f"**🎞️ Genres:** {local_details['genres']}")
            else:
                st.markdown("**🎞️ Genres:** N/A")

            st.markdown("---")

# ----------------- Popular Movies Scroll Section -----------------
st.markdown("#### Or pick from popular movies")

pages = st.session_state.popular_movies_pages

cols = st.columns([1, 10, 1])
with cols[0]:
    if st.button("⬅️", key="prev_page"):
        st.session_state.page = max(0, st.session_state.page - 1)
        st.rerun()

with cols[2]:
    if st.button("➡️", key="next_page"):
        st.session_state.page = min(len(pages) - 1, st.session_state.page + 1)
        st.rerun()

with cols[1]:
    current_page_idx = st.session_state.page
    if not (0 <= current_page_idx < len(pages)):
        current_page_idx = 0
        st.session_state.page = 0

    grid = pages[current_page_idx]
    for row_idx in range(2):
        cols_row = st.columns(5)
        for col_idx in range(5):
            idx = row_idx * 5 + col_idx
            if idx < len(grid):
                name, tmdb_id = grid[idx]
                poster_url, rating, _ = get_movie_details_tmdb(tmdb_id)

                with cols_row[col_idx]:
                    # --- Native Streamlit display for popular movies ---
                    if poster_url:
                        st.image(poster_url, use_column_width=True)
                    else:
                        st.markdown('<div style="background-color:#333; height:150px; display:flex; align-items:center; justify-content:center; border-radius:5px; color:#bbb; text-align:center; font-size:0.9em;">No Poster Available</div>', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True) # Add some space

                    st.markdown(f"**⭐ {rating if rating != 'N/A' else 'N/A'}**")
                    st.markdown(f"**{name}**")

                    if st.button("Select", key=f"pop_select_{name}_{tmdb_id}"):
                        st.session_state.favorite = name
                        st.rerun()

# ----------------- Additional Preferences -----------------
st.markdown("### Additional Preferences")

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

        if not recommendations:
            st.info("No recommendations found based on your criteria. Try different preferences!")
        else:
            for rec in recommendations:
                title = rec['title']
                tmdb_id = rec['tmdb_id']
                reason = rec['reason']

                poster_url, rating, tagline = get_movie_details_tmdb(tmdb_id)
                local_details = get_movie_details_from_df(title)

                cols_rec = st.columns([1, 4])
                with cols_rec[0]:
                    # --- Native Streamlit display for recommended movies ---
                    if poster_url:
                        st.image(poster_url, width=100)
                    else:
                        st.markdown('<div style="width:100px; height:150px; background-color:#333; display:flex; align-items:center; justify-content:center; border-radius:5px; color:#bbb; text-align:center; font-size:0.9em;">No Poster Available</div>', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True) # Add some space

                    st.markdown(f"**⭐ {rating if rating != 'N/A' else 'N/A'}**")

                with cols_rec[1]:
                    st.markdown(f"**{title}**")
                    st.markdown(f"⭐ IMDb: {rating if rating else 'N/A'}")
                    st.markdown(f"📝 {tagline if tagline else reason}")

                    if local_details:
                        actors_display = ", ".join(local_details['top_actors']) if local_details['top_actors'] else 'N/A'
                        st.markdown(f"**🎭 Actors:** {actors_display}")
                        st.markdown(f"**🎬 Director:** {local_details['director'] if local_details['director'] else 'N/A'}")
                        st.markdown(f"**🎞️ Genres:** {local_details['genres'] if local_details['genres'] else 'N/A'}")

                    st.markdown("---")

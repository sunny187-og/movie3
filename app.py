import streamlit as st
import random
from model import recommend, get_all_movies, get_all_actors, get_all_directors, get_all_genres, get_movie_details_from_df
from utils import get_movie_details as get_movie_details_tmdb

st.set_page_config(page_title="Movie Recommender", layout="wide")

# ----------------- Session State Initialization -----------------
if "favorite" not in st.session_state:
    st.session_state.favorite = None
if "page" not in st.session_state:
    st.session_state.page = 0
if "popular_movies_data" not in st.session_state:
    all_movies_items = list(get_all_movies().items())
    num_samples = min(30, len(all_movies_items))
    st.session_state.popular_movies_data = random.sample(all_movies_items, num_samples)
    st.session_state.popular_movies_pages = [st.session_state.popular_movies_data[i:i+10] for i in range(0, len(st.session_state.popular_movies_data), 10)]


# --- Helper Function for Movie Card HTML (for popular/recommended movies where simpler display is used) ---
# This helper function is not strictly needed anymore for its initial purpose due to simplification,
# but can be used for consistency if we decide to re-introduce more complex HTML later.
# For now, keeping it minimal to avoid re-introducing issues.
def get_movie_card_html_simplified(movie_name, poster_url, rating, width="100%", height="auto"):
    """Generates simplified HTML for a movie card with poster, optional rating, and title."""
    image_html = ""
    if poster_url:
        image_html = f'<img src="{poster_url}" alt="{movie_name}" style="width: 100%; height: auto; object-fit: cover; border-radius: 5px;">'
    else:
        # Placeholder for no poster
        image_html = f'''
        <div style="width: 100%; height: {height}; background-color: #333; display: flex;
                    align-items: center; justify-content: center; border-radius: 5px; text-align: center;
                    color: #bbb; font-size: 0.9em; padding: 10px; box-sizing: border-box;">
            No Poster Available
        </div>
        '''

    rating_display = ""
    if rating and rating != 'N/A':
        rating_display = f"⭐ {rating:.1f}"
    else:
        rating_display = "⭐ N/A"

    return f"""
    <div style="text-align: center; margin-bottom: 5px; width: {width};">
        {image_html}
        <div style="font-size: 0.9em; margin-top: 5px;">
            <span style="font-weight: bold;">{rating_display}</span><br>
            {movie_name}
        </div>
    </div>
    """

# ----------------- Header -----------------
st.title("🎬 Movie Recommender")

# ----------------- Favorite Movie Search Input -----------------
all_movies = get_all_movies()
fav_movie_input = st.text_input("Search for your favorite movie", key="fav_input")

if fav_movie_input:
    filtered_titles = [m_title for m_m_title in all_movies.keys() if fav_movie_input.lower() in m_m_title.lower()]
    top10 = filtered_titles[:10]
    for i, movie_title in enumerate(top10):
        if st.button(movie_title, key=f"fav_search_btn_{i}"):
            st.session_state.favorite = movie_title
            st.rerun()

# ----------------- Favorite Movie Thumbnail and Details -----------------
if st.session_state.favorite:
    st.markdown(f"**Selected Favorite:** {st.session_state.favorite}")
    tmdb_id = all_movies.get(st.session_state.favorite)

    if tmdb_id:
        poster_url, rating, tagline = get_movie_details_tmdb(tmdb_id)
        local_details = get_movie_details_from_df(st.session_state.favorite)

        fav_cols = st.columns([1, 4])

        with fav_cols[0]: # Left column for poster and its overlaid rating
            if poster_url:
                rating_html = ""
                if rating and rating != 'N/A':
                    rating_html = f'''
                    <div style="position: absolute; top: 5px; right: 5px;
                                 background-color: rgba(0, 0, 0, 0.7); color: white;
                                 padding: 3px 6px; border-radius: 5px; font-size: 0.8em;
                                 font-weight: bold; z-index: 1;">
                        ⭐ {rating:.1f}
                    </div>
                    '''
                st.markdown(
                    f"""
                    <div style="position: relative; width: 150px; height: 225px; margin-bottom: 10px;">
                        <img src="{poster_url}" alt="{st.session_state.favorite}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 5px;">
                        {rating_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Fallback box for no poster on Favorite Movie
                st.markdown(
                    f'''
                    <div style="width: 150px; height: 225px; background-color: #333; display: flex;
                                align-items: center; justify-content: center; border-radius: 5px; text-align: center;
                                color: #bbb; font-size: 1em; font-weight: bold; padding: 10px; box-sizing: border-box;
                                margin-bottom: 10px;">
                        No Poster Available
                    </div>
                    ''',
                    unsafe_allow_html=True
                )


        with fav_cols[1]: # Right column for movie details
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
                    # Use the simplified helper for consistent rendering
                    # The helper now directly handles the "No Poster" case
                    card_html_content = get_movie_card_html_simplified(name, poster_url, rating, height="150px") # Define a height for the box
                    st.markdown(card_html_content, unsafe_allow_html=True)

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

                cols_rec = st.columns([1, 4])
                with cols_rec[0]:
                    # Use the simplified helper for consistent rendering
                    # The helper now directly handles the "No Poster" case
                    card_html_content = get_movie_card_html_simplified(title, poster_url, rating, width="100px", height="150px") # Specific dimensions for recs
                    st.markdown(card_html_content, unsafe_allow_html=True)

                with cols_rec[1]:
                    st.markdown(f"**{title}**")
                    st.markdown(f"⭐ IMDb: {rating if rating else 'N/A'}")
                    st.markdown(f"📝 {tagline if tagline else reason}")
                    st.markdown("---")
                    st.markdown(f"**{title}**")
                    st.markdown(f"⭐ IMDb: {rating if rating else 'N/A'}")
                    st.markdown(f"📝 {tagline if tagline else reason}")
                    st.markdown("---")

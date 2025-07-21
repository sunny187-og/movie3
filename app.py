import streamlit as st
import random
from model import recommend, get_all_movies, get_all_actors, get_all_directors, get_all_genres, get_movie_details_from_df
from utils import get_movie_details as get_movie_details_tmdb # Renamed to avoid clash

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
    filtered_titles = [m_title for m_title in all_movies.keys() if fav_movie_input.lower() in m_title.lower()]
    top10 = filtered_titles[:10]
    for i, movie_title in enumerate(top10):
        if st.button(movie_title, key=f"fav_search_btn_{i}"):
            st.session_state.favorite = movie_title
            st.rerun()

# ----------------- Favorite Movie Thumbnail (UPDATED SECTION) -----------------
if st.session_state.favorite:
    st.markdown(f"**Selected Favorite:** {st.session_state.favorite}")
    tmdb_id = all_movies.get(st.session_state.favorite)

    if tmdb_id:
        poster_url, rating, tagline = get_movie_details_tmdb(tmdb_id) # Get TMDB details
        local_details = get_movie_details_from_df(st.session_state.favorite) # Get local DataFrame details

        fav_cols = st.columns([1, 4]) # Use columns for layout

        with fav_cols[0]: # Left column for poster and its rating
            if poster_url:
                # Use markdown with HTML/CSS for rating overlay on favorite movie poster
                st.markdown(
                    f"""
                    <div style="position: relative; width: 150px; height: 225px;">
                        <img src="{poster_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 5px;">
                        {f'''
                        <div style="position: absolute; top: 5px; right: 5px;
                                     background-color: rgba(0, 0, 0, 0.7); color: white;
                                     padding: 3px 6px; border-radius: 5px; font-size: 0.8em;
                                     font-weight: bold;">
                            ⭐ {rating:.1f}
                        </div>
                        ''' if rating and rating != 'N/A' else ''}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.write(st.session_state.favorite) # Fallback if no poster
                if rating and rating != 'N/A':
                    st.markdown(f"**⭐ {rating:.1f}**")

        with fav_cols[1]: # Right column for details
            # Display Tagline from TMDB
            if tagline:
                st.markdown(f"📝 *{tagline}*")
            else:
                st.markdown(f"📝 *No tagline available.*")

            # Display Actors from local_details
            if local_details and local_details['top_actors']:
                actors_display = ", ".join(local_details['top_actors'])
                st.markdown(f"**🎭 Actors:** {actors_display}")
            else:
                st.markdown("**🎭 Actors:** N/A")

            # Display Director from local_details
            if local_details and local_details['director']:
                st.markdown(f"**🎬 Director:** {local_details['director']}")
            else:
                st.markdown("**🎬 Director:** N/A")

            # Display Genres from local_details
            if local_details and local_details['genres']:
                st.markdown(f"**🎞️ Genres:** {local_details['genres']}")
            else:
                st.markdown("**🎞️ Genres:** N/A")

            st.markdown("---") # Separator

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
                    # Display rating first, directly above the image in popular movies
                    if rating and rating != 'N/A':
                        st.markdown(f"**⭐ {rating:.1f}**", unsafe_allow_html=True)
                    else:
                        st.markdown("⭐ N/A")

                    if poster_url:
                        st.image(poster_url, caption=name, use_container_width=True)
                    else:
                        st.write(name)

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
                    if poster_url:
                        st.markdown(
                            f"""
                            <div style="position: relative; width: 100px; height: 150px;">
                                <img src="{poster_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 5px;">
                                {f'''
                                <div style="position: absolute; top: 5px; right: 5px;
                                             background-color: rgba(0, 0, 0, 0.7); color: white;
                                             padding: 2px 5px; border-radius: 3px; font-size: 0.7em;">
                                    ⭐ {rating:.1f}
                                </div>
                                ''' if rating and rating != 'N/A' else ''}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.write(title)

                with cols_rec[1]:
                    st.markdown(f"**{title}**")
                    st.markdown(f"⭐ IMDb: {rating if rating else 'N/A'}")
                    st.markdown(f"📝 {tagline if tagline else reason}")
                    st.markdown("---")

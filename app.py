import streamlit as st
import random
 
from model import recommend, get_all_movies, get_all_actors, get_all_directors, get_all_genres, get_movie_details_from_df
from utils import get_movie_details as get_movie_details_tmdb # Renamed to avoid clash with local function

st.set_page_config(page_title="Movie Recommender", layout="wide")

# ----------------- Session State Initialization -----------------
# Initialize 'favorite' movie selection
if "favorite" not in st.session_state:
    st.session_state.favorite = None
# Initialize page for popular movies section
if "page" not in st.session_state:
    st.session_state.page = 0
# Initialize and cache popular_movies data and pages ONLY ONCE
# This prevents random shuffling every time a button is clicked
if "popular_movies_data" not in st.session_state:
    all_movies_items = list(get_all_movies().items()) # Get all movie titles and their TMDB IDs
    num_samples = min(30, len(all_movies_items)) # Sample up to 30 movies
    st.session_state.popular_movies_data = random.sample(all_movies_items, num_samples)
    # Divide sampled movies into pages (10 movies per page)
    st.session_state.popular_movies_pages = [st.session_state.popular_movies_data[i:i+10] for i in range(0, len(st.session_state.popular_movies_data), 10)]


# ----------------- Header -----------------
st.title("🎬 Movie Recommender")

# ----------------- Favorite Movie Search Input -----------------
all_movies = get_all_movies() # Dictionary: {movie_title: tmdb_id}
fav_movie_input = st.text_input("Search for your favorite movie", key="fav_input")

if fav_movie_input:
    # Filter movie titles that match the search input (case-insensitive)
    filtered_titles = [m_title for m_title in all_movies.keys() if fav_movie_input.lower() in m_title.lower()]
    top10 = filtered_titles[:10] # Show top 10 matches
    for i, movie_title in enumerate(top10):
        # Create a button for each search result
        if st.button(movie_title, key=f"fav_search_btn_{i}"):
            st.session_state.favorite = movie_title # Set selected movie as favorite
            st.rerun() # Rerun to update the display immediately

# ----------------- Favorite Movie Thumbnail and Details -----------------
if st.session_state.favorite:
    st.markdown(f"**Selected Favorite:** {st.session_state.favorite}")
    tmdb_id = all_movies.get(st.session_state.favorite) # Get TMDB ID for the favorite movie

    if tmdb_id:
        # Fetch external details (poster, rating, tagline) from TMDb API
        poster_url, rating, tagline = get_movie_details_tmdb(tmdb_id)
        # Fetch local details (genres, director, top_actors_list) from our DataFrame
        local_details = get_movie_details_from_df(st.session_state.favorite)

        # Use columns for layout: 1 for poster, 4 for details
        fav_cols = st.columns([1, 4])

        with fav_cols[0]: # Left column for poster and its overlaid rating
            if poster_url:
                # Construct HTML for the poster with rating overlay
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
                    unsafe_allow_html=True # Allow Streamlit to render raw HTML
                )
            else:
                # Fallback if no poster URL is found
                st.write(st.session_state.favorite)
                if rating and rating != 'N/A':
                    st.markdown(f"**⭐ {rating:.1f}**")

        with fav_cols[1]: # Right column for movie details
            # Display tagline
            if tagline:
                st.markdown(f"📝 *{tagline}*")
            else:
                st.markdown(f"📝 *No tagline available.*")

            # Display Actors
            if local_details and local_details['top_actors']:
                actors_display = ", ".join(local_details['top_actors'])
                st.markdown(f"**🎭 Actors:** {actors_display}")
            else:
                st.markdown("**🎭 Actors:** N/A")

            # Display Director
            if local_details and local_details['director']:
                st.markdown(f"**🎬 Director:** {local_details['director']}")
            else:
                st.markdown("**🎬 Director:** N/A")

            # Display Genres
            if local_details and local_details['genres']:
                st.markdown(f"**🎞️ Genres:** {local_details['genres']}")
            else:
                st.markdown("**🎞️ Genres:** N/A")

            st.markdown("---") # Visual separator

# ----------------- Popular Movies Scroll Section (FINAL FIX FOR CAPTION) -----------------
st.markdown("#### Or pick from popular movies")

pages = st.session_state.popular_movies_pages # Use the cached popular movie pages

# Create columns for navigation arrows and the movie grid
cols = st.columns([1, 10, 1])
with cols[0]:
    if st.button("⬅️", key="prev_page"):
        st.session_state.page = max(0, st.session_state.page - 1)
        st.rerun() # Rerun to update the page display

with cols[2]:
    if st.button("➡️", key="next_page"):
        st.session_state.page = min(len(pages) - 1, st.session_state.page + 1)
        st.rerun() # Rerun to update the page display

# Display grid of 2 rows x 5 columns within the central column
with cols[1]:
    # Ensure current page index is valid to prevent errors if data changes
    current_page_idx = st.session_state.page
    if not (0 <= current_page_idx < len(pages)):
        current_page_idx = 0
        st.session_state.page = 0

    grid = pages[current_page_idx]
    for row_idx in range(2): # Iterate for two rows
        cols_row = st.columns(5) # Create 5 columns for each row
        for col_idx in range(5): # Iterate for 5 columns
            idx = row_idx * 5 + col_idx # Calculate index within the current grid
            if idx < len(grid):
                name, tmdb_id = grid[idx] # Unpack movie title and TMDB ID
                poster_url, rating, _ = get_movie_details_tmdb(tmdb_id) # Fetch details from TMDb

                with cols_row[col_idx]: # Place elements within the specific column
                    if poster_url:
                        # Construct HTML for poster with rating overlay for popular movies
                        rating_html = ""
                        if rating and rating != 'N/A':
                            rating_html = f'''
                            <div style="position: absolute; top: 5px; right: 5px;
                                         background-color: rgba(0, 0, 0, 0.7); color: white;
                                         padding: 2px 5px; border-radius: 3px; font-size: 0.7em; font-weight: bold; z-index: 1;">
                                ⭐ {rating:.1f}
                            </div>
                            '''
                        # --- THE FIX IS HERE ---
                        # Use a single markdown block for the image, rating, and name
                        st.markdown(
                            f"""
                            <div style="position: relative; text-align: center; margin-bottom: 5px;">
                                <img src="{poster_url}" alt="{name}" style="width: 100%; height: auto; object-fit: cover; border-radius: 5px;">
                                {rating_html}
                                <div style="font-size: 0.9em; margin-top: 5px;">{name}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        # Fallback if no poster
                        st.write(name)
                        if rating and rating != 'N/A':
                            st.markdown(f"**⭐ {rating:.1f}**")

                    # Explicit "Select" button below the poster
                    if st.button("Select", key=f"pop_select_{name}_{tmdb_id}"):
                        st.session_state.favorite = name # Set selected movie as favorite
                        st.rerun() # Rerun to update favorite display

# ----------------- Additional Preferences (Selectboxes) -----------------
st.markdown("### Additional Preferences")

# Populate selectbox options dynamically from model functions
actor_options = [""] + get_all_actors()
director_options = [""] + get_all_directors()
genre_options = [""] + get_all_genres()

actor = st.selectbox("🎭 Favorite Actor", actor_options, key="actor_select")
director = st.selectbox("🎬 Favorite Director", director_options, key="director_select")
genre = st.selectbox("🎞️ Favorite Genre", genre_options, key="genre_select")
mood = st.selectbox("🧠 Your Mood", ["", "Happy", "Sad", "Excited", "Romantic", "Curious", "Dark", "Calm"], key="mood_select")


# ----------------- Recommendation Button and Display -----------------
if st.button("Recommend Movies 🎯"):
    if not st.session_state.favorite:
        st.warning("Please select a favorite movie first.")
    else:
        st.subheader("🎉 Recommended for You:")
        # Call the recommendation function from model.py
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
            # Display each recommended movie
            for rec in recommendations:
                title = rec['title']
                tmdb_id = rec['tmdb_id']
                reason = rec['reason']

                # Fetch external details for recommended movie display
                poster_url, rating, tagline = get_movie_details_tmdb(tmdb_id)

                cols_rec = st.columns([1, 4]) # Layout for recommended movie details
                with cols_rec[0]:
                    if poster_url:
                        # Construct HTML for recommended movie poster with rating overlay
                        rating_html = ""
                        if rating and rating != 'N/A':
                            rating_html = f'''
                            <div style="position: absolute; top: 5px; right: 5px;
                                         background-color: rgba(0, 0, 0, 0.7); color: white;
                                         padding: 2px 5px; border-radius: 3px; font-size: 0.7em; font-weight: bold; z-index: 1;">
                                ⭐ {rating:.1f}
                            </div>
                            '''
                        st.markdown(
                            f"""
                            <div style="position: relative; width: 100px; height: 150px;">
                                <img src="{poster_url}" alt="{title}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 5px;">
                                {rating_html}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.write(title) # Fallback if no poster

                with cols_rec[1]:
                    st.markdown(f"**{title}**")
                    st.markdown(f"⭐ IMDb: {rating if rating else 'N/A'}")
                    st.markdown(f"📝 {tagline if tagline else reason}")
                    st.markdown("---") # Separator for recommendations

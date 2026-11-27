"""ReadNext: browse manga and light novels and get recommendations.

Run from the project root:
    streamlit run app/streamlit_app.py
"""

import re
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
TITLES_PER_PAGE = 24
CARDS_PER_ROW = 6

st.set_page_config(page_title="ReadNext", page_icon="📚", layout="wide")



# Load data (cached, so it's only read once)
@st.cache_data
def load_data():
    titles = pd.read_parquet(DATA_DIR / "titles.parquet")
    recommendations = pd.read_parquet(DATA_DIR / "recommendations.parquet")
    return titles, recommendations


def has_value(value):
    """True if a field is filled in (not empty and not missing)."""
    return isinstance(value, str) and value != ""


def clean_description(text):
    """AniList descriptions contain HTML tags like <br> and <i>. Remove them."""
    if not has_value(text):
        return "No description available."
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def open_title(title_id):
    st.session_state.selected_title_id = title_id


def go_back():
    st.session_state.selected_title_id = None


titles, recommendations = load_data()
titles_by_id = titles.set_index("title_id")

if "selected_title_id" not in st.session_state:
    st.session_state.selected_title_id = None



# Title page: details + "If you liked this, read these"
def show_title_page(title_id):
    title = titles_by_id.loc[title_id]

    st.button("← Back to catalog", on_click=go_back)

    left, right = st.columns([1, 3])
    with left:
        if has_value(title.cover_image_url):
            st.image(title.cover_image_url, width="stretch")
    with right:
        st.title(title.title)
        format_name = "Light novel" if title.format == "NOVEL" else "Manga"
        score = f"{title.average_score:.0f}/100" if pd.notna(title.average_score) else "No score"
        year = f"{title.start_year:.0f}" if pd.notna(title.start_year) else "Unknown year"
        status = title.status.replace("_", " ").title() if has_value(title.status) else "Unknown status"
        st.caption(f"{format_name} · {year} · {status} · {score}")
        st.write(" ".join(f"`{genre}`" for genre in title.genres))
        st.write(clean_description(title.description))
        if has_value(title.site_url):
            st.link_button("View on AniList", title.site_url)

    st.divider()
    st.subheader("If you liked this, read these")

    recs = (
        recommendations[recommendations.title_id == title_id]
        .sort_values("recommendation_rank")
        .merge(titles, left_on="recommended_title_id", right_on="title_id", suffixes=("", "_rec"))
    )

    if recs.empty:
        st.info("No recommendations for this title yet.")
        return

    for start in range(0, len(recs), 5):
        columns = st.columns(5)
        for column, rec in zip(columns, recs.iloc[start:start + 5].itertuples()):
            with column:
                if has_value(rec.cover_image_url):
                    st.image(rec.cover_image_url, width="stretch")
                st.markdown(f"**{rec.title}**")
                st.caption(f"Match: {rec.similarity_score:.0%}")
                st.caption("Shared: " + ", ".join(rec.top_shared_tags))
                st.button("Open", key=f"rec_{rec.recommended_title_id}",
                          on_click=open_title, args=(rec.recommended_title_id,))


# Catalog page: category, search, filters and a grid of titles
def show_catalog():
    st.title("ReadNext")
    st.write("Find your next manga or light novel. Open a title to see what to read next, and why.")

    category = st.segmented_control("Category", ["Manga", "Light novels"], default="Manga")
    selected_format = "NOVEL" if category == "Light novels" else "MANGA"

    search_col, genre_col, sort_col = st.columns([2, 2, 1])
    search = search_col.text_input("Search by title", placeholder="e.g. Frieren")
    all_genres = sorted({genre for genres in titles.genres for genre in genres})
    chosen_genres = genre_col.multiselect("Genres", all_genres)
    sort_by = sort_col.selectbox("Sort by", ["Popularity", "Score", "Newest"])

    # Apply filters
    shown = titles[titles.format == selected_format]
    if search:
        shown = shown[shown.title.str.contains(search, case=False, na=False)]
    if chosen_genres:
        shown = shown[shown.genres.apply(lambda genres: all(g in genres for g in chosen_genres))]

    sort_column = {"Popularity": "popularity", "Score": "average_score", "Newest": "start_year"}[sort_by]
    shown = shown.sort_values(sort_column, ascending=False, na_position="last")

    st.caption(f"{len(shown)} titles")
    if shown.empty:
        st.info("No titles match your filters.")
        return

    # Simple pagination
    total_pages = (len(shown) - 1) // TITLES_PER_PAGE + 1
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1) if total_pages > 1 else 1
    page_titles = shown.iloc[(page - 1) * TITLES_PER_PAGE: page * TITLES_PER_PAGE]

    for start in range(0, len(page_titles), CARDS_PER_ROW):
        columns = st.columns(CARDS_PER_ROW)
        for column, title in zip(columns, page_titles.iloc[start:start + CARDS_PER_ROW].itertuples()):
            with column:
                if has_value(title.cover_image_url):
                    st.image(title.cover_image_url, width="stretch")
                st.markdown(f"**{title.title}**")
                if pd.notna(title.average_score):
                    st.caption(f"{title.average_score:.0f}/100")
                st.button("Open", key=f"title_{title.title_id}",
                          on_click=open_title, args=(title.title_id,))



# Show the right page
if st.session_state.selected_title_id is None:
    show_catalog()
else:
    show_title_page(st.session_state.selected_title_id)
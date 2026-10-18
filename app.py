"""Polished Streamlit dashboard for the MovieLens PDS mini-project."""
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

st.set_page_config(
    page_title="ReelScope | MovieLens Insights",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
      --ink: #17243a;
      --muted: #64748b;
      --line: #e4eaf2;
      --paper: #f5f7fb;
      --white: #ffffff;
      --blue: #315efb;
      --teal: #00a58a;
      --gold: #f3ac3d;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(245,247,251,.88); }
    [data-testid="stSidebar"] { background: #101b2e; border-right: 1px solid #22304a; }
    [data-testid="stSidebar"] * { color: #e7edf7; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #a9b7cc; }
    [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #1b2940; border-color: #33445f; }
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--ink); font-family: 'Manrope', sans-serif; letter-spacing: -.035em; }
    h1 { font-size: 2.15rem !important; font-weight: 800 !important; }
    h2 { font-size: 1.35rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.04rem !important; font-weight: 700 !important; }
    p, label { color: var(--muted); }
    [data-testid="stMetric"] { background: var(--white); border: 1px solid var(--line); border-radius: 15px; padding: 17px 19px; box-shadow: 0 5px 18px rgba(24,42,72,.035); }
    [data-testid="stMetricLabel"] p { color: #738198 !important; font-size: .79rem !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: var(--ink) !important; font-family: 'Manrope', sans-serif; font-size: 1.7rem !important; font-weight: 800 !important; }
    [data-testid="stMetricDelta"] { font-size: .76rem; }
    [data-testid="stTabs"] [role="tablist"] { gap: 8px; border-bottom: 1px solid var(--line); }
    [data-testid="stTabs"] button[role="tab"] { color: #748198; font-weight: 700; padding: 11px 17px; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: var(--blue); border-bottom-color: var(--blue); }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
    [data-testid="stAlert"] { border-radius: 12px; }
    .hero { background: linear-gradient(115deg, #14213a 0%, #1c3155 56%, #244a69 100%); border-radius: 20px; padding: 28px 32px; margin-bottom: 22px; color: #fff; box-shadow: 0 14px 34px rgba(20,33,58,.13); }
    .hero-kicker { color: #94b9ff; text-transform: uppercase; letter-spacing: .16em; font-size: .72rem; font-weight: 700; margin-bottom: 9px; }
    .hero-title { color: #fff; font-family: 'Manrope', sans-serif; font-size: 2rem; line-height: 1.18; letter-spacing: -.04em; font-weight: 800; margin: 0; }
    .hero-copy { color: #c5d1e2; font-size: .96rem; margin: 9px 0 0; max-width: 720px; }
    .hero-chip { display:inline-block; margin-top:18px; margin-right:8px; border:1px solid rgba(203,218,241,.24); background:rgba(255,255,255,.07); color:#e5edf8; border-radius:99px; padding:6px 11px; font-size:.75rem; font-weight:600; }
    .section-intro { color: var(--muted); font-size: .9rem; margin-top: -.55rem; margin-bottom: 1rem; }
    .card-title { color: var(--ink); font-family: 'Manrope', sans-serif; font-size: 1.06rem; font-weight: 750; margin-bottom: 2px; }
    .card-subtitle { color: var(--muted); font-size: .8rem; margin-bottom: 13px; }
    .method-pill { display:inline-block; padding:5px 10px; border-radius:99px; color:#087765; background:#e5f7f2; border:1px solid #c6eee4; font-size:.74rem; font-weight:700; }
    .status-pill { display:inline-block; padding:5px 10px; border-radius:99px; color:#17634f; background:#e4f6ee; font-size:.74rem; font-weight:700; }
    .status-pill.warn { color:#94600a; background:#fff3d9; }
    .sidebar-brand { font-family:'Manrope',sans-serif; font-size:1.28rem; color:#fff; font-weight:800; letter-spacing:-.04em; padding: .35rem 0 .1rem; }
    .sidebar-tag { color:#8fa3bf; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; font-weight:700; }
    .sidebar-note { border:1px solid #2d3d57; background:#17243a; border-radius:12px; padding:12px 13px; color:#bdc9d9; font-size:.8rem; line-height:1.5; }
    .small-note { color:#8290a5; font-size:.76rem; }
    .footer { border-top:1px solid var(--line); margin-top:34px; padding-top:16px; color:#8290a5; font-size:.76rem; }
    code { color:#274fcb; }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_summary() -> dict:
    path = RESULTS / "run_summary.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def read_result(filename: str) -> pd.DataFrame:
    path = RESULTS / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def display_table(frame: pd.DataFrame, columns: list[str], *, height: int = 350, config=None) -> None:
    shown = frame[[column for column in columns if column in frame.columns]].copy()
    st.dataframe(shown, hide_index=True, use_container_width=True, height=height, column_config=config or {})


summary = load_summary()
if not summary:
    st.markdown('<div class="hero"><div class="hero-kicker">Parallel and Distributed Systems · Mini Project</div><p class="hero-title">ReelScope</p><p class="hero-copy">Movie insights and personalized recommendations, powered by MovieLens.</p></div>', unsafe_allow_html=True)
    st.info("Run `python -m src.download_data`, then `python -m src.pipeline` to prepare the dashboard data.")
    st.stop()

popular = read_result("popular_movies.csv")
top = read_result("top_rated_movies.csv")
preferences = read_result("user_preferences.csv")
recommendations = read_result("recommendations.csv")
performance = read_result("performance.csv")
genre_summary = read_result("genre_summary.csv")
rating_distribution = read_result("rating_distribution.csv")

# User selection is in the sidebar so it remains available throughout the demo.
st.sidebar.markdown('<div class="sidebar-brand">ReelScope</div><div class="sidebar-tag">Movie intelligence</div>', unsafe_allow_html=True)
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("### Dashboard controls")
if not preferences.empty:
    user_ids = sorted(int(user_id) for user_id in preferences.userId.dropna().unique())
    default_user = int(summary.get("selected_user_id", user_ids[0]))
    selected_user = st.sidebar.selectbox(
        "Analyze user",
        user_ids,
        index=user_ids.index(default_user) if default_user in user_ids else 0,
        help="Genre preferences are available for every user. Recommendations were generated for the user shown in the run summary.",
    )
else:
    selected_user = int(summary.get("selected_user_id", 0))

spark_status = str(summary.get("spark_status", "unknown"))
if spark_status == "available":
    st.sidebar.markdown('<span class="status-pill">Spark ALS active</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<span class="status-pill warn">Fallback recommender</span>', unsafe_allow_html=True)
st.sidebar.markdown(
    f"<br><div class='sidebar-note'><b>Dataset</b><br>{summary.get('dataset', 'MovieLens')}<br><br>"
    f"<b>Execution mode</b><br>{summary.get('spark_master', 'local[*]')}<br><br>"
    "Local mode uses cores on this computer.</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("<br><span class='small-note'>Source: GroupLens Research</span>", unsafe_allow_html=True)

method_label = "Spark MLlib ALS" if spark_status == "available" else "Genre and rating baseline"
st.markdown(
    f"""<div class="hero">
      <div class="hero-kicker">Parallel and Distributed Systems · Mini Project</div>
      <p class="hero-title">Movie insights, made personal.</p>
      <p class="hero-copy">Explore rating patterns, discover audience favorites, and generate recommendations from real MovieLens data.</p>
      <span class="hero-chip">MovieLens Latest Small</span>
      <span class="hero-chip">Apache Spark</span>
      <span class="hero-chip">Python multithreading</span>
      <span class="hero-chip">{method_label}</span>
    </div>""",
    unsafe_allow_html=True,
)

st.markdown("### Dataset at a glance")
st.markdown('<div class="section-intro">A real-world rating snapshot from GroupLens Research.</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ratings analyzed", f"{int(summary.get('ratings', 0)):,}")
m2.metric("Unique users", f"{int(summary.get('users', 0)):,}")
m3.metric("Movies", f"{int(summary.get('movies', 0)):,}")
rmse = summary.get("als_test_rmse")
m4.metric("ALS test RMSE", f"{float(rmse):.3f}" if rmse is not None else "Not measured", help="Held-out rating prediction error. Lower is better; it is not an accuracy percentage.")

overview_tab, user_tab, performance_tab = st.tabs(["Overview", "User insights", "Performance & method"])

with overview_tab:
    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown('<div class="card-title">Most popular movies</div><div class="card-subtitle">Ranked by number of user ratings.</div>', unsafe_allow_html=True)
        if not popular.empty:
            popular_view = popular.head(10).copy()
            popular_view.insert(0, "Rank", range(1, len(popular_view) + 1))
            display_table(popular_view, ["Rank", "title", "rating_count", "genres"], height=395,
                          config={"title": st.column_config.TextColumn("Movie", width="large"),
                                  "rating_count": st.column_config.NumberColumn("Ratings", format="%,.0f")})
        else:
            st.info("Popular movie results are not available yet.")
    with right:
        st.markdown('<div class="card-title">Highest rated</div><div class="card-subtitle">Average rating, with at least 30 ratings per movie.</div>', unsafe_allow_html=True)
        if not top.empty:
            top_view = top.head(10).copy()
            top_view.insert(0, "Rank", range(1, len(top_view) + 1))
            display_table(top_view, ["Rank", "title", "average_rating", "rating_count", "genres"], height=395,
                          config={"title": st.column_config.TextColumn("Movie", width="large"),
                                  "average_rating": st.column_config.NumberColumn("Avg. rating", format="%.2f"),
                                  "rating_count": st.column_config.NumberColumn("Ratings", format="%,.0f")})
        else:
            st.info("High-rated movie results are not available yet.")

    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.markdown('<div class="card-title">Rating distribution</div><div class="card-subtitle">How often each score appears in the dataset.</div>', unsafe_allow_html=True)
        if not rating_distribution.empty:
            rating_chart_data = rating_distribution.copy()
            rating_chart_data["rating"] = rating_chart_data.rating.astype(str)
            rating_chart = alt.Chart(rating_chart_data).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#315efb").encode(
                x=alt.X("rating:N", title="Rating", sort=["0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0"]),
                y=alt.Y("count:Q", title="Number of ratings"),
                tooltip=[alt.Tooltip("rating:N", title="Rating"), alt.Tooltip("count:Q", title="Ratings", format=",")],
            ).properties(height=250)
            st.altair_chart(rating_chart, use_container_width=True)
    with chart_right:
        st.markdown('<div class="card-title">Top genres by average rating</div><div class="card-subtitle">Dataset-wide average; a movie can belong to multiple genres.</div>', unsafe_allow_html=True)
        if not genre_summary.empty:
            genre_chart_data = genre_summary[genre_summary.genre != "(no genres listed)"].nlargest(10, "average_rating")
            genre_chart = alt.Chart(genre_chart_data).mark_bar(cornerRadiusEnd=5, color="#00a58a").encode(
                x=alt.X("average_rating:Q", title="Average rating", scale=alt.Scale(domain=[0, 5])),
                y=alt.Y("genre:N", title=None, sort="-x"),
                tooltip=[alt.Tooltip("genre:N", title="Genre"), alt.Tooltip("average_rating:Q", title="Average", format=".2f"), alt.Tooltip("rating_count:Q", title="Ratings", format=",")],
            ).properties(height=250)
            st.altair_chart(genre_chart, use_container_width=True)

with user_tab:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### User {selected_user}")
    st.markdown('<div class="section-intro">Genre preferences are calculated from this user’s own ratings.</div>', unsafe_allow_html=True)
    if not preferences.empty:
        user_preferences = preferences[preferences.userId == selected_user].sort_values(["average_rating", "rating_count"], ascending=False).copy()
        favorite = user_preferences[user_preferences.genre != "(no genres listed)"].head(1)
        genre_count = int(user_preferences.genre.nunique())
        avg_rating = float(preferences.loc[preferences.userId == selected_user, "average_rating"].mean())
        p1, p2, p3 = st.columns(3)
        p1.metric("Genres rated", genre_count)
        p2.metric("Average score", f"{avg_rating:.2f} / 5")
        p3.metric("Top genre", favorite.iloc[0].genre if not favorite.empty else "—")

        pref_col, rec_col = st.columns([.9, 1.1], gap="large")
        with pref_col:
            st.markdown('<div class="card-title">Genre preference profile</div><div class="card-subtitle">Average rating per genre, with rating counts.</div>', unsafe_allow_html=True)
            preference_chart = alt.Chart(user_preferences.head(12)).mark_bar(cornerRadiusEnd=5, color="#315efb").encode(
                x=alt.X("average_rating:Q", title="Average rating", scale=alt.Scale(domain=[0, 5])),
                y=alt.Y("genre:N", title=None, sort="-x"),
                tooltip=[alt.Tooltip("genre:N", title="Genre"), alt.Tooltip("average_rating:Q", title="Average", format=".2f"), alt.Tooltip("rating_count:Q", title="Ratings", format=",")],
            ).properties(height=350)
            st.altair_chart(preference_chart, use_container_width=True)
        with rec_col:
            st.markdown('<div class="card-title">Recommended for you</div><div class="card-subtitle">Top unseen movies ranked by predicted rating.</div>', unsafe_allow_html=True)
            user_recs = recommendations[recommendations.userId == selected_user].copy() if "userId" in recommendations else pd.DataFrame()
            if not user_recs.empty:
                st.markdown(f'<span class="method-pill">{user_recs.iloc[0].get("method", method_label)}</span>', unsafe_allow_html=True)
                user_recs.insert(0, "Rank", range(1, len(user_recs) + 1))
                display_table(user_recs, ["Rank", "title", "genres", "predicted_rating"], height=360,
                              config={"title": st.column_config.TextColumn("Movie", width="large"),
                                      "predicted_rating": st.column_config.NumberColumn("Predicted score", format="%.2f")})
                st.caption("Predicted scores are model estimates; they can fall outside the original 0.5–5 rating range.")
            else:
                st.info(f"Recommendations were last generated for user {summary.get('selected_user_id')}. To refresh for user {selected_user}, run:")
                st.code(f"python -m src.pipeline --require-spark --benchmark-repeats 3 --user-id {selected_user}", language="powershell")

with performance_tab:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### How the implementations compare")
    st.markdown('<div class="section-intro">Same four summary tasks: popular movies, high-rated movies, rating distribution, and genre summary.</div>', unsafe_allow_html=True)
    if not performance.empty:
        perf_chart = alt.Chart(performance).mark_bar(cornerRadiusEnd=7).encode(
            x=alt.X("elapsed_seconds:Q", title="Elapsed time (seconds)"),
            y=alt.Y("method:N", title=None, sort="-x"),
            color=alt.Color("method:N", scale=alt.Scale(domain=["Sequential", "Multithreaded", "Apache Spark (aggregation)"], range=["#718096", "#00a58a", "#315efb"]), legend=None),
            tooltip=[alt.Tooltip("method:N", title="Method"), alt.Tooltip("elapsed_seconds:Q", title="Seconds", format=".3f"), alt.Tooltip("speedup_vs_sequential:Q", title="Speedup", format=".3f"), alt.Tooltip("ratings_per_second:Q", title="Ratings/sec", format=",")],
        ).properties(height=230)
        st.altair_chart(perf_chart, use_container_width=True)
        display_table(performance, ["method", "elapsed_seconds", "speedup_vs_sequential", "ratings_per_second", "workers"], height=185,
                      config={"elapsed_seconds": st.column_config.NumberColumn("Seconds", format="%.3f"),
                              "speedup_vs_sequential": st.column_config.NumberColumn("Speedup", format="%.3f×"),
                              "ratings_per_second": st.column_config.NumberColumn("Ratings / sec", format="%,.0f")})
    startup = summary.get("spark_startup_and_input_seconds_approx")
    if startup is not None:
        st.info(f"Spark startup and input materialization took about {float(startup):.2f} seconds, measured separately from the aggregation chart. Spark uses {summary.get('spark_master', 'local[*]')} on this run.")
    info_a, info_b, info_c = st.columns(3)
    with info_a:
        st.markdown("**Sequential**")
        st.caption("Runs each analysis task one after another. This is the baseline for speedup.")
    with info_b:
        st.markdown("**Multithreaded**")
        st.caption("A four-worker ThreadPoolExecutor schedules independent tasks concurrently in one Python process.")
    with info_c:
        st.markdown("**Apache Spark**")
        st.caption("DataFrame tasks run in parallel across local cores. local[*] is single-machine mode, not a cluster.")

st.markdown(
    f"<div class='footer'>Dataset: <a href='https://grouplens.org/datasets/movielens/' target='_blank'>GroupLens MovieLens</a> · "
    f"Recommendation method: {method_label} · Selected user: {selected_user} · PDS Mini Project</div>",
    unsafe_allow_html=True,
)

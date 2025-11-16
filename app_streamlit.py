# app_streamlit.py
from pathlib import Path
import asyncio
import pandas as pd
import streamlit as st

# Optional on-demand fetch (so "This Week" works without running a separate script)
try:
    from providers.tmdb import fetch_tmdb_trending
    HAVE_FETCH = True
except Exception:
    HAVE_FETCH = False

from providers.tmdb import fetch_tmdb_external_ids
from providers.omdb import fetch_omdb_rating
@st.cache_data(ttl=60*60)
def get_imdb_stats_cached(item_id: int, media_type: str):
    import asyncio
    ext = asyncio.run(fetch_tmdb_external_ids(item_id, media_type)) or {}
    imdb_id = ext.get("imdb_id")
    if not imdb_id:
        return {}
    return asyncio.run(fetch_omdb_rating(imdb_id)) or {}


from providers.tmdb import fetch_tmdb_trending, fetch_tmdb_providers  # ensure imported
@st.cache_data(ttl=60*60)  # cache for 1 hour per title/region
def get_availability_cached(item_id: int, media_type: str, region: str):
    # async provider -> sync wrapper
    import asyncio
    return asyncio.run(fetch_tmdb_providers(item_id, media_type, region))


st.set_page_config(page_title="Trending — Media Analytics", layout="wide")
DATA = Path("data")
POSTER_BASE = "https://image.tmdb.org/t/p/w342"

# --- Light/Dark toggle (simple CSS theme) ---
dark_mode = st.toggle("Dark mode", value=False, help="Toggle a simple dark/light theme.")
if dark_mode:
    st.markdown("""
        <style>
        :root { --bg:#0b0f15; --panel:#141a22; --text:#e8edf3; --muted:#a8b4c0; --border:#253041; --halo:#3aa0ff; }
        html, body, [data-testid="stAppViewContainer"] { background:var(--bg)!important; color:var(--text)!important; }
        [data-testid="stHeader"]{background:transparent!important}
        body, p, span, label, h1,h2,h3,h4,h5,h6,[data-testid="stMarkdownContainer"] *{color:var(--text)!important}
        small,.stMarkdown small{color:var(--muted)!important}

        /* Section cards */
        .segment { background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:16px 18px; margin:16px 0 20px 0; }

        /* Metrics / inputs */
        div[data-testid="stMetric"]{background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:12px}
        div[data-testid="stMetricValue"],div[data-testid="stMetricLabel"]{color:var(--text)!important}
        .stRadio>div,.stSelectbox,.stSlider,.stDataFrame{background:var(--panel)!important; border-radius:10px}

        /* Poster grid card */
        .poster-card{
            background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.00));
            border:1px solid var(--border);
            border-radius:14px; padding:10px; transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;
            overflow:hidden; position:relative; margin-bottom:18px;
        }
        .poster-img{width:100%; height:auto; border-radius:10px; display:block;}
        .poster-meta{font-size:15px; color:var(--muted); margin-top:6px}
        .poster-title{font-weight:600; margin-top:8px; font-size:20px; color:var(--text)}
        .poster-imdb{margin-top:4px; font-size:18px; font-weight:600; color:var(--text)}
        .provider-row{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; margin-bottom:4px;}
        .prov-logo{width:39px; height:39px
        ; border-radius:7px; background:#233042; padding:4px; object-fit:contain;}
        .prov-pill{display:inline-block; height:32px; line-height:30px; padding:0 10px; border-radius:7px; background:#233042; color:var(--text); font-size:11px; border:1px solid var(--border)}
        .poster-card:hover{ transform:scale(1.03); border-color: rgba(58,160,255,.85); box-shadow:0 6px 26px rgba(58,160,255,.18), 0 2px 10px rgba(0,0,0,.35); }

        /* Tighter grid spacing between rows */
        .stColumns > div { padding-bottom: 6px; }
        </style>
    """, unsafe_allow_html=True)
else:
    # Light theme polish (keeps logos same size)
    st.markdown("""
        <style>
        :root { --panel:#ffffff; --border:#e6e8ec; --text:#0f1720; --muted:#586273; --halo:#2b7fff; }
        .segment{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:16px 18px; margin:16px 0 20px 0; }
        .poster-card{ background:#fff; border:1px solid var(--border); border-radius:14px; padding:10px; transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease; margin-bottom:18px;}
        .poster-img{width:100%; height:auto; border-radius:10px;}
        .poster-title{font-weight:600; margin-top:8px; font-size:20px; color:var(--text)}
        .poster-imdb{margin-top:4px; font-size:18px; font-weight:600; color:var(--text)}
        .poster-meta{font-size:15px; color:var(--muted); margin-top:6px}
        .provider-row{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; margin-bottom:4px;}
        .prov-logo{width:39px; height:39px; border-radius:7px; background:#eef3ff; padding:4px; object-fit:contain; border:1px solid #e5ecff;}
        .prov-pill{display:inline-block; height:32px; line-height:30px; padding:0 10px; border-radius:7px; background:#eef3ff; color:#1c2735; font-size:11px; border:1px solid #e5ecff}
        .poster-card:hover{ transform:scale(1.03); border-color: var(--halo); box-shadow:0 6px 24px rgba(43,127,255,.18), 0 2px 10px rgba(16,24,40,.08); }
        .stColumns > div { padding-bottom: 6px; }
        </style>
    """, unsafe_allow_html=True)





st.title("Trending — Media Analytics")

with st.expander("About these metrics (click to expand)", expanded=False):
    st.markdown(
        """
**What you’re seeing**

- **Trending** surfaces titles getting the most attention on TMDB **today** (or **this week**).
- **Popularity** is TMDB’s relative trending score (higher = more current momentum). Not a count of views.
- **Vote average** is the average user rating (0–10).  
- **Vote count** is how many ratings a title has received.

Use **Time horizon** to switch between Today and This Week. Use **Content type** to filter.
        """
    )

# ---- Controls
col1, col2, col3, col4 = st.columns([1,1,2,1])
with col1:
    horizon = st.radio("Time horizon", ["Today", "This Week"], index=0,
                       help="‘Today’ = last 24h trending. ‘This Week’ = rolling 7 days.")
with col2:
    content_type = st.selectbox("Content type", ["All", "Movies", "TV"],
                                help="Filter to movies only, TV series only, or keep all.")
with col3:
    display_limit = st.slider("Number of titles to display", 5, 50, 20, 5,
                              help="Controls how many items appear in the table and charts.")
with col4:
    country = st.selectbox("Country", ["US","IN","GB","CA","AU","DE","FR","BR","MX"],
                           help="Used for streaming availability (watch/providers).")
show_availability = st.checkbox("Show streaming availability under posters", value=True)


tmdb_file = DATA / "tmdb_trending.parquet"
if not tmdb_file.exists():
    st.info("No TMDB data yet. Run `python run_fetch_all.py` once, or use the fetch button below.")
    # On-demand fetch (TODAY) if available
    if HAVE_FETCH and st.button("Fetch latest (Today)"):
        asyncio.run(fetch_tmdb_trending("all", "day"))
        st.rerun()
    st.stop()

df_all = pd.read_parquet(tmdb_file)
selected_window = "day" if horizon == "Today" else "week"
df = df_all[df_all.get("window", "day") == selected_window].copy()

# If there's no data for this horizon, offer to fetch it now
if df.empty:
    st.warning("No rows for the selected horizon. Pull the latest for this view.")
    if HAVE_FETCH and st.button(f"Fetch latest ({'Today' if selected_window=='day' else 'This Week'})"):
        asyncio.run(fetch_tmdb_trending("all", selected_window))
        st.rerun()
    st.stop()

# Choose the most complete batch (same timestamp for a full pull)
batch_counts = df["ts"].value_counts()
best_ts = batch_counts.index[0]
latest = df[df["ts"] == best_ts].copy()

# Apply content filter
if content_type == "Movies":
    latest = latest[latest["media_type"] == "movie"].copy()
elif content_type == "TV":
    latest = latest[latest["media_type"] == "tv"].copy()

# --- Headline metrics
st.markdown("### Snapshot")
m1, m2, m3 = st.columns(3)
total_titles = len(latest)
m1.metric("Titles in view", f"{total_titles}")

median_pop = latest["popularity"].dropna().median() if total_titles else None
m2.metric("Median popularity", f"{median_pop:.1f}" if median_pop is not None else "–",
          help="TMDB’s relative trending score (higher = more momentum).")

avg_rating = latest["vote_average"].dropna().mean() if total_titles else None
m3.metric("Average user rating", f"{avg_rating:.1f}" if avg_rating is not None else "–",
          help="Average of TMDB user ratings on a 0–10 scale.")

# --- Poster gallery (10 per row, up to 2 rows → 20 max). No deprecated args.
st.markdown("### Trending gallery")
if "poster_path" in latest.columns and latest["poster_path"].notna().any():
    gallery = latest.sort_values("popularity", ascending=False).head(min(display_limit, 20)).reset_index(drop=True)

    # Make exactly 10 columns per row
    def render_row(df_row):
        df_row = df_row.reset_index(drop=True)
        cols = st.columns(10, gap="small")

        for j, row in df_row.iterrows():
            with cols[j]:
                # Fetch availability (cached)
                avail = {}
                if show_availability:
                    try:
                        avail = get_availability_cached(int(row["id"]), row["media_type"], country) or {}
                    except Exception:
                        avail = {}
                show_list = (avail.get("flatrate") or
                            avail.get("rent") or
                            avail.get("buy") or
                            avail.get("free") or
                            avail.get("ads") or [])

                # IMDb rating (cached)
                stats = {}
                try:
                    stats = get_imdb_stats_cached(int(row["id"]), row["media_type"]) or {}
                except Exception:
                    stats = {}
                imdb_rating = stats.get("imdbRating")
                imdb_votes = (stats.get("imdbVotes") or "").replace(",", " ")
                imdb_line = f"IMDb {imdb_rating} / 10 • {imdb_votes} votes" if imdb_rating else "IMDb N/A / 10 • N/A votes"

                # Build provider badges
                badges = []
                for name, logo in show_list[:6]:
                    if logo:
                        badges.append(f'<img class="prov-logo" src="https://image.tmdb.org/t/p/w45{logo}" alt="{name}"/>')
                    else:
                        safe = (name or "Provider").replace('"','&quot;')
                        badges.append(f'<span class="prov-pill">{safe}</span>')
                if not badges and show_availability:
                    badges.append(f'<span class="prov-pill" title="No provider data for region">No info</span>')

                poster_url = f"{POSTER_BASE}{row['poster_path']}" if row.get("poster_path") else ""
                title = (row.get("title") or "").replace("<","&lt;").replace(">","&gt;")
                # cleaner meta: “movie • Popularity 290.3”
                meta = f"{(row.get('media_type') or '').lower()} • Popularity {row.get('popularity',0):.1f}"

                html = f"""
                <div class="poster-card">
                {'<img class="poster-img" src="'+poster_url+'" />' if poster_url else ''}
                <div class="poster-imdb">{imdb_line}</div>
                <div class="poster-title">{title}</div>
                <div class="poster-meta">{meta}</div>
                <div class="provider-row">{''.join(badges)}</div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

      

    # First row (0..9)
    render_row(gallery.iloc[0:10])
    # Second row (10..19) if present
    if len(gallery) > 10:
        render_row(gallery.iloc[10:20])
else:
    st.caption("No poster images available in this pull.")


# --- Detailed table (dark-mode aware, compact, larger font) ---


# --- Popularity leaderboard
import plotly.express as px

import altair as alt
import streamlit as st

st.set_page_config(layout="wide")

# ---- Side-by-side layout: table (left) + chart (right)
# How many rows are actually visible
rows_to_show = min(display_limit, len(latest))

# Make columns a bit flexible but still left (table) / right (chart)
# 1 : 1.4 works well on most screens
left, right = st.columns((1, 1.4))

with left:
    st.markdown("### Detailed results")

    # Build the data you show now
    tbl = (
        latest[["title", "media_type", "popularity", "vote_average", "vote_count", "release_date"]]
        .sort_values("popularity", ascending=False)
        .head(display_limit)
        .reset_index(drop=True)
    )

    # Add a 1-based row index column named '#'
    tbl.index = tbl.index + 1
    tbl = tbl.rename_axis("#").reset_index()

    if dark_mode:
        table_styles = [
            {"selector": "table",
             "props": [("background-color", "#141a22"),
                       ("color", "#e8edf3"),
                       ("border-collapse", "collapse"),
                       ("font-size", "14px")]},
            {"selector": "th",
             "props": [("background-color", "#0b0f15"),
                       ("color", "#e8edf3"),
                       ("font-weight", "600"),
                       ("border", "1px solid #253041"),
                       ("padding", "6px 12px")]},
            {"selector": "td",
             "props": [("border", "1px solid #253041"),
                       ("padding", "6px 12px")]},
            {"selector": "tbody tr:nth-child(even)",
             "props": [("background-color", "#161c25")]},
            {"selector": "tbody tr:hover",
             "props": [("background-color", "#1f2733")]},
        ]
    else:
        table_styles = [
            {"selector": "table",
             "props": [("background-color", "#ffffff"),
                       ("color", "#0f1720"),
                       ("border-collapse", "collapse"),
                       ("font-size", "14px")]},
            {"selector": "th",
             "props": [("background-color", "#f5f6fa"),
                       ("color", "#0f1720"),
                       ("font-weight", "600"),
                       ("border", "1px solid #e6e8ec"),
                       ("padding", "6px 12px")]},
            {"selector": "td",
             "props": [("border", "1px solid #e6e8ec"),
                       ("padding", "6px 12px")]},
            {"selector": "tbody tr:nth-child(even)",
             "props": [("background-color", "#fafafa")]},
            {"selector": "tbody tr:hover",
             "props": [("background-color", "#eef3ff")]},
        ]

    styled = (
        tbl.style
        .set_table_styles(table_styles)
        .set_properties(
            subset=["popularity", "vote_average", "vote_count"],
            **{"text-align": "right"},
        )
    )

    st.markdown(styled.to_html(), unsafe_allow_html=True)

with right:
    st.markdown("### Popularity leaderboard")

    # Build a compact data frame for the chart
    chart_df = (
        latest[["title", "popularity"]]
        .sort_values("popularity", ascending=False)
        .head(display_limit)
        .reset_index(drop=True)
    )

    # Theme bits for dark vs light
    if dark_mode:
        axis_color = "#e8edf3"
        grid_color = "#263243"
        bar_color  = "#6aa8ff"
        bg_color   = "#0b0f15"
    else:
        axis_color = "#0f1720"
        grid_color = "#e6e8ec"
        bar_color  = "#4e89ff"
        bg_color   = "white"

    # 🔹 Make bar thickness and chart height depend on how many rows we show
    # - fewer rows -> thicker bars / shorter chart
    # - more rows  -> thinner bars / taller chart
    bar_size = max(16, int(40 - 0.8 * rows_to_show))     # never less than 16
    chart_height = int(40 * rows_to_show + 80)           # header + margin

    # Base bars
    bars = (
        alt.Chart(chart_df)
        .mark_bar(size=bar_size, color=bar_color)
        .encode(
            x=alt.X(
                "title:N",
                sort=None,
                axis=alt.Axis(title=None, labels=False, ticks=False, domain=False),
            ),
            y=alt.Y(
                "popularity:Q",
                axis=alt.Axis(title="Popularity"),
            ),
            tooltip=["title:N", "popularity:Q"],
        )
        .properties(height=chart_height)
    )

    # Labels only for Top-3 bars, with larger font
    top3_labels = (
        alt.Chart(chart_df)
        .transform_window(rank="rank(popularity)")
        .transform_filter("datum.rank <= 3")
        .mark_text(
            dy=-8,
            fontSize=16,
            fontWeight="bold",
            color=axis_color,
        )
        .encode(
            x=alt.X("title:N", sort=None,
                    axis=alt.Axis(title=None, labels=False, ticks=False, domain=False)),
            y="popularity:Q",
            text="title:N",
        )
    )

    chart = (
        bars + top3_labels
    ).configure_axis(
        labelColor=axis_color,
        titleColor=axis_color,
        gridColor=grid_color,
        domainColor=bg_color,
        tickColor=axis_color,
    ).configure_axisX(
        domain=False, ticks=False, labels=False
    ).configure_view(
        stroke=None, strokeOpacity=0, fill=bg_color
    )

    st.altair_chart(chart, use_container_width=True)



# --- Quality vs audience scale
st.markdown("### Quality vs audience scale")
st.caption("Higher **vote average** with larger **vote count** suggests broadly liked, widely rated titles.")
scatter_df = latest[["title","vote_average","vote_count"]].dropna()
fig_scatter = px.scatter(
    scatter_df,
    x="vote_count",
    y="vote_average",
    hover_name="title",
    color_discrete_sequence=["#3aa0ff"],
)
fig_scatter.update_layout(
    template="plotly_dark" if dark_mode else "plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e8edf3" if dark_mode else "#0f1720"),
)
st.plotly_chart(fig_scatter, use_container_width=True)


# --- API perf section
API_visible = st.toggle("API Performance", value=False, help="Toggle a API Performance dashboard.")
if API_visible:
    st.markdown("---")
    st.header("API Performance")
    st.caption("Response time and payload size for recent TMDB trending calls.")
    perf_file = DATA / "perf_log.parquet"
    if perf_file.exists():
        perf = pd.read_parquet(perf_file).sort_values("ts", ascending=False)
        st.dataframe(perf, use_container_width=True)
        st.line_chart(perf, x="ts", y="latency_ms", color="provider")
        st.line_chart(perf, x="ts", y="bytes", color="provider")
    else:
        st.info("No performance logs yet. They’re created when you fetch data.")


st.caption(
        "Data & images: The Movie Database (TMDB). "
        "This product uses the TMDB API but is not endorsed or certified by TMDB."
    )
st.caption(
        "Ratings: OMDb API. This product uses the OMDb API but is not endorsed or certified by OMDb."
    )

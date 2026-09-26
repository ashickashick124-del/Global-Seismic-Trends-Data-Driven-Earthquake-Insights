"""
Streamlit Dashboard - Green & White Theme
Run with: streamlit run app.py
"""

import os
import textwrap
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Global Seismic Trends",
    page_icon="🌍",
    layout="wide"
)

# ============================================================
# COLORS
# ============================================================

GREEN = "#2E7D32"
DARK_GREEN = "#1B5E20"
LIGHT_GREEN = "#E8F5E9"
MID_GREEN = "#66BB6A"
PALE_GREEN = "#F4FBF4"
BLACK = "#222222"
GREY = "#666666"
WHITE = "#FFFFFF"
BORDER = "#D7E8D7"

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
<style>

.stApp {{
    background-color: {PALE_GREEN};
    color: {BLACK};
}}

.main .block-container {{
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}}

/* Sidebar */

section[data-testid="stSidebar"] {{
    background-color: {GREEN};
}}

section[data-testid="stSidebar"] * {{
    color: white !important;
}}

/* Main headings */

h1, h2, h3 {{
    color: {DARK_GREEN} !important;
}}

h1 {{ font-weight: 700 !important; }}
h2 {{ font-weight: 650 !important; }}
h3 {{ font-weight: 650 !important; }}

/* Header */

.dashboard-header {{
    background-color: {WHITE};
    border-left: 6px solid {GREEN};
    border-bottom: 1px solid {BORDER};
    padding: 22px 25px;
    margin-bottom: 25px;
    border-radius: 6px;
}}

.dashboard-title {{
    color: {DARK_GREEN};
    font-size: 30px;
    font-weight: 700;
    margin: 0;
}}

.dashboard-subtitle {{
    color: {GREY};
    font-size: 15px;
    margin-top: 5px;
}}

/* Sidebar brand block */

.sidebar-brand-title {{
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 2px;
}}

.sidebar-brand-subtitle {{
    font-size: 13px;
    margin-bottom: 20px;
    opacity: 0.85;
}}

/* KPI cards */

div[data-testid="stMetric"] {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-top: 4px solid {GREEN};
    border-radius: 8px;
    padding: 15px;
}}

div[data-testid="stMetric"] label {{
    color: {GREY} !important;
    font-weight: 500 !important;
}}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {DARK_GREEN} !important;
    font-weight: 700 !important;
}}

/* Buttons */

.stButton > button {{
    background-color: {GREEN};
    color: white;
    border: none;
    border-radius: 5px;
    font-weight: 600;
}}

.stButton > button:hover {{
    background-color: {DARK_GREEN};
    color: white;
}}

/* Select boxes */

div[data-baseweb="select"] > div {{
    background-color: white;
    border-color: #C8D8C8;
}}

/* Dataframe */

div[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
}}

/* Divider */

hr {{ border-color: {BORDER} !important; }}

/* Footer */

.footer {{
    text-align: center;
    color: {GREY};
    font-size: 13px;
    padding: 25px;
}}

</style>
""",
    unsafe_allow_html=True
)


def render_html(html: str) -> None:
    """
    Render a block of raw HTML safely.
    textwrap.dedent() strips the common leading whitespace that
    Markdown would otherwise misread as an indented code block
    (this is what was causing the raw <div> tags to show up as
    literal text instead of rendering).
    """
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


def plotly_layout(**overrides):
    """
    Merge one-off chart settings into the shared PLOTLY_LAYOUT
    without ever passing the same keyword (e.g. 'yaxis') twice.
    """
    layout = dict(PLOTLY_LAYOUT)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(layout.get(key), dict):
            merged = dict(layout[key])
            merged.update(value)
            layout[key] = merged
        else:
            layout[key] = value
    return layout


# ============================================================
# PLOTLY THEME
# ============================================================

PLOTLY_LAYOUT = dict(
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=dict(color=BLACK),
    xaxis=dict(gridcolor="#E5E5E5", zerolinecolor="#D5D5D5"),
    yaxis=dict(gridcolor="#E5E5E5", zerolinecolor="#D5D5D5"),
)

# ============================================================
# DATABASE CONFIG
# ============================================================

DB_CONFIG = {
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "my-password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "3306"),
    "database": os.getenv("DB_NAME", "earthquake_db"),
}


@st.cache_resource
def get_engine():
    url = (
        f"mysql+mysqlconnector://"
        f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/"
        f"{DB_CONFIG['database']}"
    )
    return create_engine(url)


@st.cache_data(ttl=600)
def load_data():
    try:
        engine = get_engine()
        return pd.read_sql(
            "SELECT * FROM earthquakes",
            engine,
            parse_dates=["time", "updated"]
        )
    except Exception:
        st.warning("MySQL connection unavailable. Using earthquake_final.csv instead.")
        return pd.read_csv("earthquake_final.csv", parse_dates=["time", "updated"])


df = load_data()

for column in ["mag", "depth_km", "latitude", "longitude", "year", "tsunami", "sig"]:
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

df["tsunami"] = df["tsunami"].fillna(0)

# ============================================================
# SIDEBAR
# ============================================================

render_html("""
    <div class="sidebar-brand-title">🌍 SEISMIC</div>
    <div class="sidebar-brand-subtitle">Global Earthquake Dashboard</div>
""")

st.sidebar.markdown("### Filters")

years = sorted(df["year"].dropna().unique().tolist())

if years:
    year_range = st.sidebar.select_slider(
        "Year range", options=years, value=(years[0], years[-1])
    )
else:
    year_range = (0, 9999)

min_mag = float(df["mag"].min())
max_mag = float(df["mag"].max())

mag_range = st.sidebar.slider(
    "Magnitude range", min_value=min_mag, max_value=max_mag,
    value=(min_mag, max_mag), step=0.1
)

countries = sorted(df["country"].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect("Country / Region", countries, placeholder="All regions")
tsunami_only = st.sidebar.checkbox("Tsunami-triggering events only")

st.sidebar.divider()
st.sidebar.markdown("### Dataset")
st.sidebar.write(f"Total records: **{len(df):,}**")
if years:
    st.sidebar.write(f"Years covered: **{years[0]} – {years[-1]}**")
st.sidebar.write("Source: USGS")

# ============================================================
# FILTER DATA
# ============================================================

filtered = df[
    (df["year"] >= year_range[0]) & (df["year"] <= year_range[1]) &
    (df["mag"] >= mag_range[0]) & (df["mag"] <= mag_range[1])
].copy()

if selected_countries:
    filtered = filtered[filtered["country"].isin(selected_countries)]

if tsunami_only:
    filtered = filtered[filtered["tsunami"] == 1]

# ============================================================
# HEADER
# ============================================================

render_html("""
    <div class="dashboard-header">
        <div class="dashboard-title">🌍 Global Seismic Trends</div>
        <div class="dashboard-subtitle">Data-Driven Earthquake Insights</div>
    </div>
""")

st.write(
    "Explore global earthquake activity, magnitude patterns, "
    "geographical distribution and seismic characteristics."
)

# ============================================================
# KPI CARDS
# ============================================================

if len(filtered) > 0:
    total_events = len(filtered)
    avg_magnitude = filtered["mag"].mean()
    strongest = filtered["mag"].max()
    tsunami_events = int(filtered["tsunami"].sum())
else:
    total_events = avg_magnitude = strongest = tsunami_events = 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Earthquakes", f"{total_events:,}")
k2.metric("Average Magnitude", f"{avg_magnitude:.2f}")
k3.metric("Strongest Magnitude", f"{strongest:.2f}")
k4.metric("Tsunami Events", f"{tsunami_events:,}")

st.divider()

# ============================================================
# MAP
# ============================================================

st.subheader("Earthquake Epicenter Map")
st.caption("Geographical distribution of recorded earthquake events.")

if len(filtered) > 0:
    map_limit = 8000
    map_df = filtered.nlargest(map_limit, "mag").copy() if len(filtered) > map_limit else filtered.copy()

    fig_map = px.scatter_geo(
        map_df, lat="latitude", lon="longitude",
        color="mag", size="mag",
        hover_name="place",
        hover_data={
            "mag": ":.2f", "depth_km": ":.1f", "country": True,
            "time": True, "latitude": False, "longitude": False
        },
        projection="natural earth",
        color_continuous_scale=["#C8E6C9", "#66BB6A", "#2E7D32", "#1B5E20"],
    )

    fig_map.update_geos(
        showland=True, landcolor="#F0F0F0",
        showocean=True, oceancolor="#E8F5E9",
        showcountries=True, countrycolor="#BBBBBB",
        coastlinecolor="#888888",
    )

    fig_map.update_layout(
        paper_bgcolor=WHITE, plot_bgcolor=WHITE, height=520,
        margin=dict(l=0, r=0, t=0, b=0),
        font=dict(color=BLACK),
        coloraxis_colorbar=dict(title="Magnitude", tickfont=dict(color=BLACK)),
    )

    st.plotly_chart(fig_map, width="stretch")
else:
    st.info("No earthquakes match the selected filters.")

# ============================================================
# YEARLY TREND + MAGNITUDE
# ============================================================

c1, c2 = st.columns(2)

with c1:
    st.subheader("Earthquakes per Year")
    yearly = filtered.groupby("year").size().reset_index(name="count")
    if len(yearly) > 0:
        fig_year = px.bar(yearly, x="year", y="count")
        fig_year.update_traces(marker_color=GREEN)
        fig_year.update_layout(**plotly_layout(height=380, title="Number of recorded earthquakes"))
        st.plotly_chart(fig_year, width="stretch")
    else:
        st.info("No yearly data available.")

with c2:
    st.subheader("Magnitude Distribution")
    if len(filtered) > 0:
        fig_mag = px.histogram(filtered, x="mag", nbins=30)
        fig_mag.update_traces(marker_color=MID_GREEN)
        fig_mag.update_layout(**plotly_layout(height=380, title="Distribution of earthquake magnitudes"))
        st.plotly_chart(fig_mag, width="stretch")
    else:
        st.info("No magnitude data available.")

# ============================================================
# COUNTRY + DEPTH
# ============================================================

c3, c4 = st.columns(2)

with c3:
    st.subheader("Top 10 Countries / Regions")
    top_countries = filtered["country"].dropna().value_counts().head(10).reset_index()
    top_countries.columns = ["country", "count"]
    if len(top_countries) > 0:
        fig_country = px.bar(top_countries, x="count", y="country", orientation="h")
        fig_country.update_traces(marker_color=GREEN)
        fig_country.update_layout(
            **plotly_layout(height=400, yaxis=dict(categoryorder="total ascending"))
        )
        st.plotly_chart(fig_country, width="stretch")
    else:
        st.info("No country data available.")

with c4:
    st.subheader("Depth Category Breakdown")
    depth_counts = filtered["depth_category"].value_counts().reset_index()
    depth_counts.columns = ["depth_category", "count"]
    if len(depth_counts) > 0:
        fig_depth = px.pie(depth_counts, names="depth_category", values="count", hole=0.4)
        fig_depth.update_traces(marker=dict(colors=[GREEN, MID_GREEN, "#A5D6A7"]))
        fig_depth.update_layout(paper_bgcolor=WHITE, font=dict(color=BLACK), height=400)
        st.plotly_chart(fig_depth, width="stretch")
    else:
        st.info("No depth data available.")

# ============================================================
# SEISMIC CHARACTERISTICS
# ============================================================

st.divider()
st.subheader("Seismic Characteristics")

a1, a2, a3, a4 = st.columns(4)

if len(filtered) > 0:
    shallow_events = int(filtered["is_shallow"].sum()) if "is_shallow" in filtered.columns else 0
    destructive_events = int(filtered["is_destructive"].sum()) if "is_destructive" in filtered.columns else 0
    deepest = filtered["depth_km"].max()
    region_count = filtered["country"].nunique()
else:
    shallow_events = destructive_events = deepest = region_count = 0

a1.metric("Shallow Events", f"{shallow_events:,}")
a2.metric("Destructive Events", f"{destructive_events:,}")
a3.metric("Deepest Event", f"{deepest:.1f} km")
a4.metric("Regions Covered", f"{region_count:,}")

# ============================================================
# STRONGEST EARTHQUAKES
# ============================================================

st.divider()
st.subheader("Strongest Earthquakes in Selected Data")

if len(filtered) > 0:
    strongest_df = (
        filtered[["time", "place", "country", "mag", "depth_km", "tsunami"]]
        .sort_values("mag", ascending=False)
        .head(10)
        .copy()
    )
    strongest_df["mag"] = strongest_df["mag"].round(2)
    strongest_df["depth_km"] = strongest_df["depth_km"].round(1)
    strongest_df["tsunami"] = strongest_df["tsunami"].map({0: "No", 1: "Yes"})
    strongest_df.columns = ["Time", "Location", "Country", "Magnitude", "Depth (km)", "Tsunami"]
    st.dataframe(strongest_df, width="stretch", hide_index=True)
else:
    st.info("No earthquake events match the current filters.")

# ============================================================
# SQL ANALYTICAL INSIGHTS
# ============================================================

st.divider()
st.subheader("SQL Analytical Insights")
st.caption("Run analytical queries directly against the MySQL database.")

QUERIES = {
    "Top 10 strongest earthquakes": """
        SELECT id, time, place, mag, depth_km FROM earthquakes
        ORDER BY mag DESC LIMIT 10
    """,
    "Top 10 deepest earthquakes": """
        SELECT id, time, place, mag, depth_km FROM earthquakes
        ORDER BY depth_km DESC LIMIT 10
    """,
    "Average magnitude per magType": """
        SELECT magType, ROUND(AVG(mag),2) AS avg_magnitude, COUNT(*) AS n
        FROM earthquakes GROUP BY magType ORDER BY avg_magnitude DESC
    """,
    "Earthquakes per year": """
        SELECT year, COUNT(*) AS total FROM earthquakes
        GROUP BY year ORDER BY year
    """,
    "Tsunami count per year": """
        SELECT year, SUM(tsunami) AS tsunami_count FROM earthquakes
        GROUP BY year ORDER BY year
    """,
    "Count by alert level": """
        SELECT alert, COUNT(*) AS total FROM earthquakes
        GROUP BY alert ORDER BY total DESC
    """,
    "Reviewed vs automatic": """
        SELECT status, COUNT(*) AS total FROM earthquakes GROUP BY status
    """,
    "Top 5 countries by average magnitude": """
        SELECT country, ROUND(AVG(mag),2) AS avg_mag, COUNT(*) AS n
        FROM earthquakes GROUP BY country HAVING n >= 5
        ORDER BY avg_mag DESC LIMIT 5
    """,
    "Deep-focus earthquakes by region": """
        SELECT country, COUNT(*) AS deep_focus_count FROM earthquakes
        WHERE depth_km > 300 GROUP BY country ORDER BY deep_focus_count DESC
    """,
}

choice = st.selectbox("Choose an analysis", list(QUERIES.keys()))

if st.button("Run SQL Analysis"):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result_df = pd.read_sql(text(QUERIES[choice]), conn)
        st.success("Query executed successfully.")
        st.dataframe(result_df, width="stretch", hide_index=True)
    except Exception as e:
        st.error(f"Query unavailable: {e}")

# ============================================================
# DATA PREVIEW
# ============================================================

with st.expander("View filtered dataset preview"):
    preview_columns = [
        c for c in ["id", "time", "place", "country", "mag", "depth_km", "tsunami", "alert"]
        if c in filtered.columns
    ]
    st.dataframe(filtered[preview_columns].head(100), width="stretch", hide_index=True)

# ============================================================
# FOOTER
# ============================================================

render_html("""
    <div class="footer">
        <b>Global Seismic Trends</b><br>
        Earthquake data · analysis · visualization<br>
        Data-Driven Earthquake Insights
    </div>
""")
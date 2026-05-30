# pip install fastf1
import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
import matplotlib.colors as mcolors
from fastf1.plotting import get_team_color
import warnings

warnings.filterwarnings("ignore")
from datetime import datetime
import plotly.graph_objects as go
import streamlit as st
from consts import *

fastf1.Cache.enable_cache("./streamlit_app/cache")

st.title("Intro")

switched_season = False  # switch ce je bila zamenjana sezona
# izbira sezone
with st.form("season_selector"):
    SEASON = st.slider(
        "Izbor sezone: ",
        2018,
        datetime.now().year,
        value=2025 if "season" not in st.session_state else st.session_state.season,
    )
    season_submitted = st.form_submit_button("Potrdi sezono")

if season_submitted:
    if st.session_state.get("season") != SEASON:
        st.session_state.selected_races = []  # reset
        switched_season = True

    st.session_state.season = SEASON

SEASON = st.session_state.get("season", 2025)
st.write(f"Prikazujem podatke za sezono {SEASON}.")

schedule = fastf1.get_event_schedule(SEASON)
num_races = schedule["RoundNumber"].max()
RACES = range(1, num_races + 1)

race_names = [
    schedule[schedule["RoundNumber"] == r]["EventName"].values[0] for r in RACES
]
RACES = race_names
selected_races_default = (
    st.session_state.selected_races
    if "selected_races" in st.session_state and st.session_state.selected_races
    else RACES
)
if switched_season:
    st.session_state.selected_races = RACES
    switched_season = False

# izbira dirk
with st.form("race_selector"):
    selected_races = st.multiselect(
        "Izberite dirke",
        RACES,
        default=selected_races_default,
        key="selected_races_input",
    )
    submitted_races = st.form_submit_button("Potrdi izbiro")

if submitted_races:
    st.session_state.selected_races = selected_races

selected_races = st.session_state.get("selected_races", RACES)


@st.cache_data(show_spinner="Pripravljam podatke...")
def graf_komulativnih_tock(season: int):
    # --- Kumulativne točke konstruktorjev ---
    points_rows = []
    for race in RACES:
        try:
            session = fastf1.get_session(season, race, "R")
            session.load(laps=False, telemetry=False, weather=False, messages=False)
            res = session.results[["TeamName", "Points"]].copy()
            res["Race"] = race
            res["RoundNumber"] = list(RACES).index(race) + 1
            points_rows.append(res)
        except Exception as e:
            st.warning(f"Error loading {race}: {e}")

    df_points = pd.concat(points_rows, ignore_index=True)

    team_pts = (
        df_points.groupby(["RoundNumber", "Race", "TeamName"])["Points"]
        .sum()
        .reset_index()
        .sort_values("RoundNumber")
    )
    team_pts["CumulativePoints"] = team_pts.groupby("TeamName")["Points"].cumsum()

    team_results = team_pts.groupby("TeamName")["Points"].sum().index.tolist()

    # Barve ekip
    try:
        _s = fastf1.get_session(season, 1, "R")
        _s.load(laps=False, telemetry=False, weather=False, messages=False)
        team_colors = {t: get_team_color(t, session=_s) for t in team_results}
    except:
        cmap = [
            f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            for r, g, b, _ in (plt.cm.tab20(i / 20) for i in range(len(team_results)))
        ]
        team_colors = {t: cmap[i] for i, t in enumerate(team_results)}

    # Plotly line chart
    fig = go.Figure()

    for team in team_results:
        d = team_pts[team_pts["TeamName"] == team]
        color = team_colors.get(team, "#888888")
        fig.add_trace(
            go.Scatter(
                x=d["RoundNumber"],
                y=d["CumulativePoints"],
                mode="lines+markers",
                name=team,
                line=dict(color=color, width=2.5),
                marker=dict(size=5),
                hovertemplate=f"<b>{team}</b><br>Dirka: %{{x}}<br>Točke: %{{y}}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(
            text=f"Komulativni seštevek točk konstruktorjev — sezona {season}",
            font=dict(color="white", size=16),
        ),
        paper_bgcolor="#2B2B2B",
        plot_bgcolor="#3B3B3B",
        font=dict(color="#aaaaaa"),
        xaxis=dict(
            title="Dirka sezone",
            gridcolor="#555555",
            linecolor="#333355",
        ),
        yaxis=dict(
            title="Kumulativne točke",
            gridcolor="#555555",
            linecolor="#333355",
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0.2)",
            font=dict(color="white"),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)


graf_komulativnih_tock(SEASON)

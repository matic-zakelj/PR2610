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

fastf1.Cache.enable_cache("./cache")

SEASON = st.session_state.season

# STREAMLIT
st.title("Hello, Streamlit!")
compound_compare_race = st.selectbox(
    "Dirka za primerjavo trdot", st.session_state.selected_races
)


# Funkcije
def load_race_laps(season: int, race_name: str) -> pd.DataFrame:
    """Naloži in filtrira kroge ene dirke"""
    session = fastf1.get_session(season, race_name, "R")
    session.load(laps=True, weather=False, telemetry=False, messages=False)

    laps = session.laps.copy()

    # Ohrani samo veljavne, natančne kroge (brez SC, VSC, pit in/out)
    laps = laps.pick_accurate()
    laps = laps[laps["PitOutTime"].isna() & laps["PitInTime"].isna()]

    # Pretvori LapTime v sekunde
    laps["LapTime_s"] = laps["LapTime"].dt.total_seconds()

    # Odstrani osamelce (> 3σ od mediane za vsako trdoto)
    def remove_outliers(group):
        med = group["LapTime_s"].median()
        sd = group["LapTime_s"].std()
        return group[np.abs(group["LapTime_s"] - med) < 3 * sd]

    laps = laps.groupby("Compound", group_keys=False).apply(remove_outliers)

    laps["Race"] = race_name
    laps["Season"] = season

    # Ohrani samo pomebne stolpce
    keep = [
        "Race",
        "Season",
        "Driver",
        "Team",
        "LapNumber",
        "Compound",
        "TyreLife",
        "LapTime_s",
    ]
    return laps[[c for c in keep if c in laps.columns]].dropna(
        subset=["LapTime_s", "TyreLife"]
    )


# Naredimo regresijsko premico
def degradation_slope(group: pd.DataFrame) -> float:
    """Vrne naklon linearne regresije LapTime/TyreLife (s/krog)."""
    if len(group) < MIN_LAPS_FOR_FIT:
        return np.nan
    slope, *_ = stats.linregress(group["TyreLife"], group["LapTime_s"])
    return slope


def primerjava_gum_na_1_dirki():
    all_laps = []
    try:
        df = load_race_laps(SEASON, compound_compare_race)
        all_laps.append(df)
    except Exception as e:
        st.error(f"NAPAKA: {e}")
        return

    if not all_laps:
        st.error("Ni bilo mogoče naložiti dirke.")
        return

    laps_all = pd.concat(all_laps, ignore_index=True)

    if DRIVERS:
        laps_all = laps_all[laps_all["Driver"].isin(DRIVERS)]

    fig = go.Figure()

    compounds = laps_all["Compound"].unique()

    for compound in compounds:
        data = laps_all[laps_all["Compound"] == compound]
        color = COMPOUND_COLORS.get(compound, "#888888")

        # Scatter
        fig.add_trace(
            go.Scatter(
                x=data["TyreLife"],
                y=data["LapTime_s"],
                mode="markers",
                name=compound,
                marker=dict(color=color, size=4, opacity=0.2),
                legendgroup=compound,
                showlegend=True,
                hovertemplate=f"<b>{compound}</b><br>TyreLife: %{{x}}<br>LapTime: %{{y:.2f}}s<extra></extra>",
            )
        )

        # Regresijska premica
        if len(data) >= MIN_LAPS_FOR_FIT:
            m, b, r, p, _ = stats.linregress(data["TyreLife"], data["LapTime_s"])
            xfit = np.linspace(data["TyreLife"].min(), data["TyreLife"].max(), 100)
            yfit = m * xfit + b
            fig.add_trace(
                go.Scatter(
                    x=xfit,
                    y=yfit,
                    mode="lines",
                    name=f"{compound} trend ({m:+.3f} s/kr)",
                    line=dict(color=color, width=2.5),
                    legendgroup=compound,
                    showlegend=True,
                    hovertemplate=f"<b>{compound} trend</b><br>TyreLife: %{{x:.1f}}<br>LapTime: %{{y:.2f}}s<extra></extra>",
                )
            )

    fig.update_layout(
        title=dict(
            text=f"Degradacija pnevmatik — {compound_compare_race} {SEASON}",
            font=dict(color="white", size=16),
        ),
        paper_bgcolor="#2B2B2B",
        plot_bgcolor="#3B3B3B",
        font=dict(color="#aaaaaa"),
        xaxis=dict(title="TyreLife (krogi od menjave)", gridcolor="#555555"),
        yaxis=dict(title="Čas kroga (s)", gridcolor="#555555"),
        legend=dict(bgcolor="rgba(0,0,0,0.2)", font=dict(color="white")),
        hovermode="closest",
    )

    st.plotly_chart(fig, use_container_width=True)


primerjava_gum_na_1_dirki()

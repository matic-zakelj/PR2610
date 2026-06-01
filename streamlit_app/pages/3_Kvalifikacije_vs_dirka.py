import warnings

import fastf1
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import pearsonr, spearmanr

warnings.filterwarnings("ignore")
fastf1.Cache.enable_cache("./streamlit_app/cache")


SEASON = st.session_state.get("season", 2025)

if "selected_races" not in st.session_state:
    schedule = fastf1.get_event_schedule(SEASON, include_testing=False)
    st.session_state.selected_races = schedule[schedule["RoundNumber"] > 0][
        "EventName"
    ].tolist()

RACES = st.session_state.selected_races

st.title("Kvalifikacije vs. dirka")

race = st.selectbox("Izberi dirko", RACES)


LAYOUT = dict(
    paper_bgcolor="#2B2B2B",
    plot_bgcolor="#3B3B3B",
    font=dict(color="#aaaaaa"),
)


def styled_layout(title: str, xaxis_title="", yaxis_title="", **kwargs):
    xaxis_extra = kwargs.pop("xaxis", {})
    yaxis_extra = kwargs.pop("yaxis", {})
    xaxis = dict(title=xaxis_title, gridcolor="#555555")
    yaxis = dict(title=yaxis_title, gridcolor="#555555")
    xaxis.update(xaxis_extra)
    yaxis.update(yaxis_extra)

    layout = dict(
        **LAYOUT,
        title=dict(text=title, font=dict(color="white", size=15)),
        xaxis=xaxis,
        yaxis=yaxis,
        legend=dict(bgcolor="rgba(0,0,0,0.2)", font=dict(color="white")),
    )
    layout.update(kwargs)
    return layout


def load_race_results(season: int, race_name: str) -> pd.DataFrame:
    session = fastf1.get_session(season, race_name, "R")
    session.load(laps=False, telemetry=False, weather=False, messages=False)

    cols = [
        c
        for c in [
            "Abbreviation",
            "FullName",
            "TeamName",
            "GridPosition",
            "Position",
            "Status",
            "Points",
        ]
        if c in session.results.columns
    ]
    df = session.results[cols].copy()
    df["GridPosition"] = pd.to_numeric(df["GridPosition"], errors="coerce")
    df["Position"] = pd.to_numeric(df["Position"], errors="coerce")
    df = df.dropna(subset=["GridPosition", "Position"])
    df = df[df["GridPosition"] > 0]
    return df.sort_values("Position")



def season_correlations(season: int, races: tuple) -> pd.DataFrame:
    rows = []
    for race_name in races:
        try:
            df = load_race_results(season, race_name)
            if len(df) < 5:
                continue
            rho, p_value = spearmanr(df["GridPosition"], df["Position"])
            rows.append(
                {
                    "Dirka": race_name,
                    "Spearman": rho,
                    "P-vrednost": p_value,
                    "Stevilo voznikov": len(df),
                }
            )
        except Exception:
            pass
    return pd.DataFrame(rows)


df = load_race_results(SEASON, race)



spearman_corr, spearman_p = spearmanr(df["GridPosition"], df["Position"])
pearson_corr, pearson_p = pearsonr(df["GridPosition"], df["Position"])

st.subheader("Štartni položaj in končna uvrstitev")
st.caption(
    "Vsaka točka predstavlja enega voznika. Diagonalna črta pomeni, da je voznik "
    "končal na istem mestu, kot je začel dirko."
)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df["GridPosition"],
        y=df["Position"],
        mode="markers+text",
        text=df["Abbreviation"],
        textposition="top center",
        marker=dict(size=12, color="#E10600", line=dict(color="white", width=1)),
        hovertemplate=(
            "<b>%{text}</b><br>Start: %{x}<br>Cilj: %{y}<extra></extra>"
        ),
        name="Vozniki",
    )
)

limit = int(max(df["GridPosition"].max(), df["Position"].max()))
fig.add_trace(
    go.Scatter(
        x=list(range(1, limit + 1)),
        y=list(range(1, limit + 1)),
        mode="lines",
        line=dict(color="#aaaaaa", dash="dash"),
        name="Start = cilj",
        hoverinfo="skip",
    )
)

fig.update_layout(
    **styled_layout(
        f"{race} {SEASON}: kvalifikacije vs. rezultat",
        xaxis_title="Štartni položaj",
        yaxis_title="Končna uvrstitev",
        xaxis=dict(
            title="Štartni položaj",
            gridcolor="#555555",
            autorange="reversed",
        ),
        yaxis=dict(
            title="Končna uvrstitev",
            gridcolor="#555555",
            autorange="reversed",
        ),
        height=550,
    )
)
st.plotly_chart(fig, use_container_width=True)

st.write(
    f"Spearmanova korelacija je **{spearman_corr:.3f}**, Pearsonova korelacija pa "
    f"**{pearson_corr:.3f}**. Višja pozitivna vrednost pomeni, da so boljše "
    "kvalifikacije bolj povezane z boljšim rezultatom."
)

st.dataframe(
    df[
        [
            "Abbreviation",
            "TeamName",
            "GridPosition",
            "Position",
            "Status",
            "Points",
        ]
    ].rename(
        columns={
            "Abbreviation": "Voznik",
            "TeamName": "Ekipa",
            "GridPosition": "Start",
            "Position": "Cilj",
            "Status": "Status",
            "Points": "Tocke",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.divider()

st.subheader("Sezonski povzetek")
st.caption(
    "Graf prikazuje Spearmanovo korelacijo med štartnim položajem in končno "
    "uvrstitvijo za izbrane dirke."
)

season_df = season_correlations(SEASON, tuple(RACES))

if not season_df.empty:
    fig2 = go.Figure()
    fig2.add_trace(
        go.Bar(
            x=season_df["Dirka"],
            y=season_df["Spearman"],
            marker_color="#E10600",
            name="Spearman",
            hovertemplate="<b>%{x}</b><br>Spearman: %{y:.3f}<extra></extra>",
        )
    )
    fig2.add_hline(
        y=season_df["Spearman"].mean(),
        line_dash="dash",
        line_color="#aaaaaa",
        annotation_text=f"Povprečje = {season_df['Spearman'].mean():.2f}",
    )
    fig2.update_layout(
        **styled_layout(
            f"Sezona {SEASON}: povezava kvalifikacij in rezultata",
            xaxis_title="Dirka",
            yaxis_title="Spearman rho",
            xaxis=dict(title="Dirka", gridcolor="#555555", tickangle=45),
            height=520,
        )
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(season_df.round(3), use_container_width=True, hide_index=True)


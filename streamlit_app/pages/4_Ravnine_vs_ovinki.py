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

st.title("Ravnine vs. ovinki")

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


def corr(df: pd.DataFrame, xcol: str, ycol: str) -> dict:
    s, sp = spearmanr(df[xcol], df[ycol])
    p, pp = pearsonr(df[xcol], df[ycol])
    return {
        "Metrika": xcol,
        "Cilj": ycol,
        "Spearman": s,
        "Spearman p": sp,
        "Pearson": p,
        "Pearson p": pp,
    }


def corner_eff(session, driver: str, corners_data: pd.DataFrame, window_m=80) -> float:
    laps = session.laps.pick_driver(driver).pick_quicklaps()
    if laps.empty:
        return np.nan

    fastest = laps.pick_fastest()
    if fastest is None or pd.isna(fastest["LapTime"]):
        return np.nan

    tel = fastest.get_car_data().add_distance().copy()
    if tel.empty or "Distance" not in tel.columns or "Speed" not in tel.columns:
        return np.nan

    corner_speeds = []
    for _, corner in corners_data.iterrows():
        distance = corner.get("Distance", np.nan)
        if pd.isna(distance):
            continue

        chunk = tel[
            (tel["Distance"] >= distance - window_m)
            & (tel["Distance"] <= distance + window_m)
        ]
        if len(chunk) < 3:
            continue

        corner_speeds.append(chunk["Speed"].min())

    if not corner_speeds:
        return np.nan

    return float(np.mean(corner_speeds))


@st.cache_data(show_spinner="Nalagam telemetrijo dirke...")
def load_speed_data(season: int, race_name: str, window_m=80) -> pd.DataFrame:
    session = fastf1.get_session(season, race_name, "R")
    session.load(laps=True, telemetry=True, weather=False, messages=False)

    results = session.results[["Abbreviation", "Position"]].copy()
    results = results.rename(
        columns={"Abbreviation": "Driver", "Position": "FinishPosition"}
    )
    results["FinishPosition"] = pd.to_numeric(
        results["FinishPosition"], errors="coerce"
    )
    results = results.dropna(subset=["Driver", "FinishPosition"])

    quick_laps = session.laps.pick_quicklaps().copy()
    if quick_laps.empty or "SpeedST" not in quick_laps.columns:
        return pd.DataFrame()

    straight_metric = (
        quick_laps.groupby("Driver")["SpeedST"]
        .median()
        .rename("StraightSpeed")
        .reset_index()
    )

    pace_metric = (
        quick_laps.groupby("Driver")["LapTime"]
        .median()
        .rename("MedianRacePace")
        .reset_index()
    )
    pace_metric["MedianRacePaceSec"] = pace_metric[
        "MedianRacePace"
    ].dt.total_seconds()
    pace_metric = pace_metric.drop(columns=["MedianRacePace"])

    corners = session.get_circuit_info().corners.copy()
    corner_rows = []
    for driver in results["Driver"].dropna().unique():
        value = corner_eff(session, driver, corners, window_m=window_m)
        corner_rows.append({"Driver": driver, "CornerEfficiency": value})

    corner_metric = pd.DataFrame(corner_rows).dropna()

    merged = (
        results.merge(straight_metric, on="Driver", how="left")
        .merge(corner_metric, on="Driver", how="left")
        .merge(pace_metric, on="Driver", how="left")
    )
    merged = merged.dropna(
        subset=[
            "FinishPosition",
            "StraightSpeed",
            "CornerEfficiency",
            "MedianRacePaceSec",
        ]
    )
    return merged.sort_values("FinishPosition")


@st.cache_data(show_spinner="Računam sezonski povzetek...")
def season_speed_summary(season: int, races: tuple) -> pd.DataFrame:
    rows = []
    for race_name in races:
        try:
            df = load_speed_data(season, race_name)
            if len(df) < 5:
                continue

            straight_finish = spearmanr(df["StraightSpeed"], df["FinishPosition"])[0]
            corner_finish = spearmanr(df["CornerEfficiency"], df["FinishPosition"])[0]
            straight_pace = spearmanr(df["StraightSpeed"], df["MedianRacePaceSec"])[0]
            corner_pace = spearmanr(
                df["CornerEfficiency"], df["MedianRacePaceSec"]
            )[0]

            rows.append(
                {
                    "Dirka": race_name,
                    "Ravnine vs rezultat": straight_finish,
                    "Ovinki vs rezultat": corner_finish,
                    "Ravnine vs tempo": straight_pace,
                    "Ovinki vs tempo": corner_pace,
                    "Mocnejsi rezultat": "Ovinki"
                    if abs(corner_finish) > abs(straight_finish)
                    else "Ravnine",
                    "Mocnejsi tempo": "Ovinki"
                    if abs(corner_pace) > abs(straight_pace)
                    else "Ravnine",
                }
            )
        except Exception:
            pass
    return pd.DataFrame(rows)


df = load_speed_data(SEASON, race)


reports = pd.DataFrame(
    [
        corr(df, "StraightSpeed", "FinishPosition"),
        corr(df, "CornerEfficiency", "FinishPosition"),
        corr(df, "StraightSpeed", "MedianRacePaceSec"),
        corr(df, "CornerEfficiency", "MedianRacePaceSec"),
    ]
)

st.subheader("Primerjava metrik na eni dirki")
st.caption(
    "StraightSpeed predstavlja hitrost na ravninah, CornerEfficiency pa povprečno "
    "hitrost v območjih ovinkov."
)

col1, col2 = st.columns(2)

with col1:
    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(
            x=df["StraightSpeed"],
            y=df["FinishPosition"],
            mode="markers+text",
            text=df["Driver"],
            textposition="top center",
            marker=dict(size=12, color="#1f77b4", line=dict(color="white", width=1)),
            hovertemplate="<b>%{text}</b><br>SpeedST: %{x}<br>Cilj: %{y}<extra></extra>",
        )
    )
    fig1.update_layout(
        **styled_layout(
            "Ravnine in rezultat",
            xaxis_title="SpeedST",
            yaxis_title="Končna uvrstitev",
            yaxis=dict(
                title="Končna uvrstitev",
                gridcolor="#555555",
                autorange="reversed",
            ),
            height=480,
        )
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(
            x=df["CornerEfficiency"],
            y=df["FinishPosition"],
            mode="markers+text",
            text=df["Driver"],
            textposition="top center",
            marker=dict(size=12, color="#E10600", line=dict(color="white", width=1)),
            hovertemplate="<b>%{text}</b><br>Ovinki: %{x:.1f}<br>Cilj: %{y}<extra></extra>",
        )
    )
    fig2.update_layout(
        **styled_layout(
            "Ovinki in rezultat",
            xaxis_title="CornerEfficiency",
            yaxis_title="Končna uvrstitev",
            yaxis=dict(
                title="Končna uvrstitev",
                gridcolor="#555555",
                autorange="reversed",
            ),
            height=480,
        )
    )
    st.plotly_chart(fig2, use_container_width=True)

st.dataframe(reports.round(3), use_container_width=True, hide_index=True)

finish_rows = reports[reports["Cilj"] == "FinishPosition"].copy()
finish_rows["AbsSpearman"] = finish_rows["Spearman"].abs()
best = finish_rows.sort_values("AbsSpearman", ascending=False).iloc[0]
st.write(
    f"Za končni rezultat je na tej dirki močnejši signal **{best['Metrika']}** "
    f"(Spearman = **{best['Spearman']:.3f}**)."
)

st.divider()

st.subheader("Sezonski povzetek")


if st.button("Izračunaj sezonski povzetek"):
    season_df = season_speed_summary(SEASON, tuple(RACES))

    if season_df.empty:
        st.warning("Sezonskega povzetka ni bilo mogoče izračunati.")
    else:
        x = season_df["Dirka"]
        fig3 = go.Figure()
        fig3.add_trace(
            go.Bar(
                x=x,
                y=season_df["Ravnine vs rezultat"].abs(),
                name="Ravnine",
                marker_color="#1f77b4",
            )
        )
        fig3.add_trace(
            go.Bar(
                x=x,
                y=season_df["Ovinki vs rezultat"].abs(),
                name="Ovinki",
                marker_color="#E10600",
            )
        )
        fig3.update_layout(
            **styled_layout(
                f"Sezona {SEASON}: ravnine in ovinki",
                xaxis_title="Dirka",
                yaxis_title="Abs Spearman rho",
                xaxis=dict(title="Dirka", gridcolor="#555555", tickangle=45),
                barmode="group",
                height=560,
            )
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.dataframe(season_df.round(3), use_container_width=True, hide_index=True)

        stronger_finish = season_df["Mocnejsi rezultat"].value_counts()
        st.write(
            "Pri povezavi s končnim rezultatom je bila pogosteje močnejša metrika: "
            f"**{stronger_finish.idxmax()}**."
        )

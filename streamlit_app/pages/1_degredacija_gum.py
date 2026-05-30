# pip install fastf1
import fastf1
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.graph_objects as go
import plotly.express as px
import warnings
import streamlit as st
from consts import *

warnings.filterwarnings("ignore")
fastf1.Cache.enable_cache("./streamlit_app/cache")

SEASON = st.session_state.season

st.title("Degradacija pnevmatik")

compound_compare_race = st.selectbox(
    "Dirka za primerjavo trdot", st.session_state.selected_races
)

#  Pomožne funkcije

LAYOUT = dict(
    paper_bgcolor="#2B2B2B",
    plot_bgcolor="#3B3B3B",
    font=dict(color="#aaaaaa"),
)


def styled_layout(title: str, xaxis_title="", yaxis_title="", **kwargs):
    return dict(
        **LAYOUT,
        title=dict(text=title, font=dict(color="white", size=15)),
        xaxis=dict(title=xaxis_title, gridcolor="#555555", tickangle=35),
        yaxis=dict(title=yaxis_title, gridcolor="#555555"),
        legend=dict(bgcolor="rgba(0,0,0,0.2)", font=dict(color="white")),
        **kwargs,
    )


@st.cache_data(show_spinner="Nalagam kroge dirke...")
def load_race_laps(season: int, race_name: str) -> pd.DataFrame:
    session = fastf1.get_session(season, race_name, "R")
    session.load(laps=True, weather=False, telemetry=False, messages=False)
    laps = session.laps.copy()
    laps = laps.pick_accurate()
    laps = laps[laps["PitOutTime"].isna() & laps["PitInTime"].isna()]
    laps["LapTime_s"] = laps["LapTime"].dt.total_seconds()

    def remove_outliers(group):
        med = group["LapTime_s"].median()
        sd = group["LapTime_s"].std()
        return group[np.abs(group["LapTime_s"] - med) < 3 * sd]

    laps = laps.groupby("Compound", group_keys=False).apply(remove_outliers)
    laps["Race"] = race_name
    laps["Season"] = season
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


def degradation_slope(group: pd.DataFrame) -> float:
    if len(group) < MIN_LAPS_FOR_FIT:
        return np.nan
    slope, *_ = stats.linregress(group["TyreLife"], group["LapTime_s"])
    return slope


@st.cache_data(show_spinner="Nalagam vse dirke...")
def get_all_laps_and_slopes(season: int, races: tuple):
    all_laps = []
    progress = st.progress(0, text="Nalagam dirke...")
    for i, race in enumerate(races):
        try:
            all_laps.append(load_race_laps(season, race))
        except Exception as e:
            st.warning(f"NAPAKA pri {race}: {e}")
        progress.progress((i + 1) / len(races), text=f"Nalagam: {race}")
    progress.empty()

    if not all_laps:
        raise RuntimeError("Ni bilo mogoče naložiti nobene dirke.")

    laps_all = pd.concat(all_laps, ignore_index=True)
    if DRIVERS:
        laps_all = laps_all[laps_all["Driver"].isin(DRIVERS)]

    slopes = (
        laps_all.groupby(["Race", "Compound"])
        .apply(degradation_slope)
        .reset_index(name="Slope_s_per_lap")
    )
    return laps_all, slopes


laps_all, slopes = get_all_laps_and_slopes(
    SEASON, tuple(st.session_state.selected_races)
)

#  Graf 1: Scatter + regresija po trdotah za eno dirko


def graf_degradacija_1_dirka():
    st.subheader("Degradacija pnevmatik — ena dirka")
    st.caption(
        "Vsaka točka je en krog enega voznika. Regresijska premica pokaže povprečno "
        "degradacijo trdote — bolj strm naklon pomeni hitrejšo izgubo časa na krog. "
        "R² in naklon sta prikazana v legendi."
    )

    try:
        laps = load_race_laps(SEASON, compound_compare_race)
    except Exception as e:
        st.error(f"NAPAKA: {e}")
        return

    if DRIVERS:
        laps = laps[laps["Driver"].isin(DRIVERS)]

    compounds = [c for c in ALL_TYRES if c in laps["Compound"].unique()]

    fig = go.Figure()
    for compound in compounds:
        data = laps[laps["Compound"] == compound]
        color = COMPOUND_COLORS.get(compound, "#888888")

        fig.add_trace(
            go.Scatter(
                x=data["TyreLife"],
                y=data["LapTime_s"],
                mode="markers",
                name=compound,
                marker=dict(color=color, size=5, opacity=0.25),
                legendgroup=compound,
                showlegend=True,
                hovertemplate=(
                    f"<b>{compound}</b><br>"
                    "TyreLife: %{x}<br>LapTime: %{y:.2f}s<extra></extra>"
                ),
            )
        )

        if len(data) >= MIN_LAPS_FOR_FIT:
            m, b, r, p, _ = stats.linregress(data["TyreLife"], data["LapTime_s"])
            r2 = r**2
            xfit = np.linspace(data["TyreLife"].min(), data["TyreLife"].max(), 100)
            fig.add_trace(
                go.Scatter(
                    x=xfit,
                    y=m * xfit + b,
                    mode="lines",
                    name=f"{compound}  {m:+.3f} s/kr  R²={r2:.2f}",
                    line=dict(color=color, width=2.5),
                    legendgroup=compound,
                    showlegend=True,
                    hovertemplate=(
                        f"<b>{compound} trend</b><br>"
                        "TyreLife: %{x:.1f}<br>LapTime: %{y:.2f}s<extra></extra>"
                    ),
                )
            )

    fig.update_layout(
        **styled_layout(
            f"Degradacija pnevmatik — {compound_compare_race} {SEASON}",
            xaxis_title="TyreLife (krogi od menjave)",
            yaxis_title="Čas kroga (s)",
            hovermode="closest",
        )
    )
    st.plotly_chart(fig, use_container_width=True)


#  Graf 2: Violin distribucija časov po trdotah ─


def graf_violin_trdote():
    st.subheader("Distribucija časov krogov po trdotah — ena dirka")
    st.caption(
        "Violin plot prikaže celotno porazdelitev časov krogov za vsako trdoto. "
        "Širši del pomeni več krogov pri tej hitrosti. Vgrajeni box plot pokaže mediano in kvartile."
    )

    try:
        laps = load_race_laps(SEASON, compound_compare_race)
    except Exception as e:
        st.error(f"NAPAKA: {e}")
        return

    compounds = [c for c in ALL_TYRES if c in laps["Compound"].unique()]

    fig = go.Figure()
    for compound in compounds:
        data = laps[laps["Compound"] == compound]["LapTime_s"]
        color = COMPOUND_COLORS.get(compound, "#888888")
        fig.add_trace(
            go.Violin(
                y=data,
                name=compound,
                box_visible=True,
                meanline_visible=True,
                fillcolor=color,
                line_color=color,
                opacity=0.75,
                showlegend=False,
                hovertemplate=f"<b>{compound}</b><br>%{{y:.2f}}s<extra></extra>",
            )
        )

    fig.update_layout(
        **styled_layout(
            f"Distribucija časov krogov po trdotah — {compound_compare_race} {SEASON}",
            yaxis_title="Čas kroga (s)",
        )
    )
    st.plotly_chart(fig, use_container_width=True)


#  Graf 3: Heatmap degradacije (spojina × dirka)


def graf_heatmap_degradacije():
    st.subheader("Heatmap degradacije: trdota × dirka")
    st.caption(
        "Naklon linearne regresije (s/krog) za vsako kombinacijo trdote in dirke. "
        "Zelena = počasna degradacija (dobro), rdeča = hitra degradacija (slabo). "
        "Vrednost 0 pomeni, da se čas kroga s trdoto ne spreminja."
    )

    pivot = slopes.pivot(index="Race", columns="Compound", values="Slope_s_per_lap")
    pivot = pivot.reindex(columns=[c for c in ALL_TYRES if c in pivot.columns])
    pivot = pivot.reindex(st.session_state.selected_races)

    vabs = max(
        abs(slopes["Slope_s_per_lap"].min()), abs(slopes["Slope_s_per_lap"].max())
    )

    text = [
        [
            f"{pivot.loc[r, c]:.3f}" if not pd.isna(pivot.loc[r, c]) else "—"
            for c in pivot.columns
        ]
        for r in pivot.index
    ]

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values.tolist(),
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale="RdYlGn_r",
            zmid=0,
            zmin=-vabs,
            zmax=vabs,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=11, color="black"),
            colorbar=dict(
                title=dict(text="Degradacija (s/krog)", font=dict(color="#aaaaaa")),
                tickfont=dict(color="#aaaaaa"),
            ),
            hovertemplate="<b>%{y}</b><br>%{x}<br>%{z:.3f} s/kr<extra></extra>",
        )
    )

    fig.update_layout(
        **styled_layout(
            f"Hitrost degradacije po dirki in trdoti — sezona {SEASON}",
            xaxis_title="Trdota",
            yaxis_title="Dirka",
            yaxis_autorange="reversed",
            height=max(400, len(pivot) * 32 + 150),
        )
    )
    st.plotly_chart(fig, use_container_width=True)


#  Tabela: povzetek degradacije


def tabela_povzetek():
    st.subheader("Povzetek degradacije po trdotah")
    st.caption(
        "Statistični povzetek naklonov degradacije za vsako trdoto čez vse izbrane dirke."
    )

    summary = (
        slopes.groupby("Compound")["Slope_s_per_lap"]
        .agg(["mean", "median", "std", "min", "max", "count"])
        .round(4)
        .reset_index()
    )
    summary.columns = [
        "Trdota",
        "Povprečje",
        "Mediana",
        "Std",
        "Min",
        "Max",
        "Število dirk",
    ]
    summary = summary[summary["Trdota"].isin(ALL_TYRES)].sort_values("Mediana")

    st.dataframe(summary, use_container_width=True, hide_index=True)

    # Najboljša / najslabša trdota po dirki
    st.caption("Trdota z najhitrejšo in najpočasnejšo degradacijo na vsaki dirki.")
    worst = slopes.loc[slopes.groupby("Race")["Slope_s_per_lap"].idxmax()].copy()
    best = slopes.loc[slopes.groupby("Race")["Slope_s_per_lap"].idxmin()].copy()

    merged = (
        worst.rename(
            columns={
                "Slope_s_per_lap": "Najhitrejša deg.",
                "Compound": "Najslabša trdota",
            }
        )
        .merge(
            best.rename(
                columns={
                    "Slope_s_per_lap": "Najpočasnejša deg.",
                    "Compound": "Najboljša trdota",
                }
            ),
            on="Race",
        )
        .rename(columns={"Race": "Dirka"})
    )

    avg_lap = (
        laps_all.groupby("Race")["LapTime_s"]
        .median()
        .reset_index()
        .rename(columns={"Race": "Dirka", "LapTime_s": "Mediana časa (s)"})
    )
    avg_lap["Mediana časa (s)"] = avg_lap["Mediana časa (s)"].round(3)

    merged = merged.merge(avg_lap, on="Dirka")

    st.dataframe(
        merged[
            [
                "Dirka",
                "Mediana časa (s)",
                "Najboljša trdota",
                "Najpočasnejša deg.",
                "Najslabša trdota",
                "Najhitrejša deg.",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


#  Render ─

graf_degradacija_1_dirka()
st.divider()
graf_violin_trdote()
st.divider()
graf_heatmap_degradacije()
st.divider()
tabela_povzetek()

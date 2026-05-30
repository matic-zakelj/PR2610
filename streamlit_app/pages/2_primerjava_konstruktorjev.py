# pip install fastf1 scikit-learn
import fastf1
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
from fastf1.plotting import get_team_color
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
import streamlit as st
from consts import *

warnings.filterwarnings("ignore")

fastf1.Cache.enable_cache("./streamlit_app/cache")

SEASON = st.session_state.season
RACES = st.session_state.selected_races

st.title("Zmogljivost konstruktorjev")


# Pomožne funkcije

@st.cache_data(show_spinner="Nalagam kroge dirke...")
def load_race_laps(season: int, race_name: str) -> pd.DataFrame:
    session = fastf1.get_session(season, race_name, 'R')
    session.load(laps=True, weather=False, telemetry=False, messages=False)
    laps = session.laps.copy()
    laps = laps.pick_accurate()
    laps = laps[laps['PitOutTime'].isna() & laps['PitInTime'].isna()]
    laps['LapTime_s'] = laps['LapTime'].dt.total_seconds()

    def remove_outliers(group):
        med = group['LapTime_s'].median()
        sd  = group['LapTime_s'].std()
        return group[np.abs(group['LapTime_s'] - med) < 3 * sd]

    laps = laps.groupby('Compound', group_keys=False).apply(remove_outliers)
    laps['Race']   = race_name
    laps['Season'] = season
    keep = ['Race', 'Season', 'Driver', 'Team', 'LapNumber',
            'Compound', 'TyreLife', 'LapTime_s']
    return laps[[c for c in keep if c in laps.columns]].dropna(
        subset=['LapTime_s', 'TyreLife'])


@st.cache_data(show_spinner="Pripravljam podatke za vse dirke...")
def get_laps_dry(season: int, races: tuple) -> pd.DataFrame:
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
        return pd.DataFrame()

    laps_all = pd.concat(all_laps, ignore_index=True)
    if DRIVERS:
        laps_all = laps_all[laps_all['Driver'].isin(DRIVERS)]
    return laps_all[laps_all['Compound'].isin(CHOSEN_TYRES)].copy()


@st.cache_data(show_spinner=False)
def get_team_colors(season: int, team_list: tuple) -> dict:
    try:
        _s = fastf1.get_session(season, 1, 'R')
        _s.load(laps=False, telemetry=False, weather=False, messages=False)
        return {t: get_team_color(t, session=_s) for t in team_list}
    except:
        import matplotlib.pyplot as plt
        cmap = plt.cm.tab20.colors
        return {t: f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                for t, (r, g, b, *_) in zip(team_list, cmap)}


def normalize_laptime(group):
    fastest = group['LapTime_s'].min()
    group = group.copy()
    group['LapTimePct'] = (group['LapTime_s'] / fastest - 1) * 100
    return group


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
        **kwargs,
    )


# Nalaganje podatkov

laps_dry = get_laps_dry(SEASON, tuple(RACES))

if laps_dry.empty:
    st.error("Ni podatkov za izbrane dirke.")
    st.stop()

laps_teams = laps_dry.groupby('Race', group_keys=False).apply(normalize_laptime)

team_overall = (
    laps_teams
    .groupby('Team')
    .agg(MedianPct=('LapTimePct', 'median'),
         StdPct=('LapTimePct', 'std'),
         LapCount=('LapTimePct', 'count'))
    .reset_index()
    .sort_values('MedianPct')
)
team_order  = team_overall['Team'].tolist()
team_colors = get_team_colors(SEASON, tuple(team_order))

# Round number za vsako dirko
race_round = {r: i + 1 for i, r in enumerate(RACES)}
laps_teams['Round'] = laps_teams['Race'].map(race_round)


# Graf 1: Violin plot

def graf_violin():
    st.subheader("Distribucija časov krogov po ekipah")
    st.caption(
        "Violin plot prikaže celotno porazdelitev relativnih časov krogov za vsako ekipo. "
        "Širši del pomeni več krogov pri tej hitrosti. Ekipe so razvrščene od najhitrejše do najpočasnejše."
    )

    fig = go.Figure()
    for team in team_order:
        data  = laps_teams[laps_teams['Team'] == team]['LapTimePct']
        color = team_colors.get(team, '#888888')
        fig.add_trace(go.Violin(
            y=data,
            name=team,
            box_visible=True,
            meanline_visible=True,
            fillcolor=color,
            opacity=0.75,
            line_color=color,
            showlegend=False,
            hovertemplate=f"<b>{team}</b><br>%{{y:.3f}}%<extra></extra>",
        ))

    fig.update_layout(**styled_layout(
        f"Distribucija relativnih časov krogov — sezona {SEASON}",
        yaxis_title="% nad najhitrejšim krogom dirke",
    ))
    st.plotly_chart(fig, use_container_width=True)


# Graf 2: Trend zmogljivosti skozi sezono

def graf_trend_sezone():
    st.subheader("Trend zmogljivosti ekip skozi sezono")
    st.caption(
        "Prikazuje povprečno relativno hitrost ekipe na vsaki dirki. "
        "Padajoča krivulja pomeni izboljšanje, naraščajoča pa poslabšanje glede na konkurenco."
    )

    team_race = (
        laps_teams
        .groupby(['Team', 'Race', 'Round'])['LapTimePct']
        .median()
        .reset_index()
        .sort_values('Round')
    )

    # Selector za ekipe
    selected = st.multiselect(
        "Izberi ekipe za prikaz",
        team_order,
        default=team_order[:5],
        key="trend_teams",
    )

    fig = go.Figure()
    for team in selected:
        d     = team_race[team_race['Team'] == team]
        color = team_colors.get(team, '#888888')

        # Scatter točke
        fig.add_trace(go.Scatter(
            x=d['Round'], y=d['LapTimePct'],
            mode='markers',
            name=team,
            marker=dict(color=color, size=7),
            legendgroup=team,
            showlegend=True,
            hovertemplate=f"<b>{team}</b><br>Dirka %{{x}}<br>%{{y:.3f}}%<extra></extra>",
        ))

        # Trend premica (linearna regresija)
        if len(d) >= 3:
            m, b, *_ = stats.linregress(d['Round'], d['LapTimePct'])
            xfit = np.array([d['Round'].min(), d['Round'].max()])
            fig.add_trace(go.Scatter(
                x=xfit, y=m * xfit + b,
                mode='lines',
                line=dict(color=color, width=2, dash='dot'),
                legendgroup=team,
                showlegend=False,
                hoverinfo='skip',
            ))

    fig.update_layout(**styled_layout(
        f"Trend zmogljivosti skozi sezono {SEASON}",
        xaxis_title="Dirka (round)",
        yaxis_title="Mediana % nad najhitrejšim krogom",
        legend=dict(bgcolor="rgba(0,0,0,0.2)", font=dict(color="white")),
    ))
    st.plotly_chart(fig, use_container_width=True)


# Graf 3: Heatmap ekipa × dirka

def graf_heatmap():
    st.subheader("Heatmap zmogljivosti: ekipa × dirka")
    st.caption(
        "Vsaka celica prikazuje mediano relativnega časa kroga ekipe na posamezni dirki. "
        "Zelena = bližje najhitrejšemu, rdeča = večje zaostajanje. Siva = ni podatkov."
    )

    pivot = (
        laps_teams
        .groupby(['Team', 'Race'])['LapTimePct']
        .median()
        .reset_index()
        .pivot(index='Team', columns='Race', values='LapTimePct')
    )
    pivot = pivot.loc[[t for t in team_order if t in pivot.index]]
    pivot = pivot[[r for r in RACES if r in pivot.columns]]

    text = [[f"{v:.2f}" if not np.isnan(v) else "—"
             for v in row] for row in pivot.values]

    fig = go.Figure(go.Heatmap(
        z=pivot.values.tolist(),
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale='RdYlGn_r',
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=10, color="black"),
        colorbar=dict(
            title=dict(text="% nad najhitrejšim", font=dict(color="#aaaaaa")),
            tickfont=dict(color="#aaaaaa"),
        ),
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{z:.2f}%<extra></extra>",
    ))
    fig.update_layout(**styled_layout(
        f"Relativna zmogljivost po dirki in ekipi — sezona {SEASON}",
        xaxis_title="Dirka",
        yaxis_title="Ekipa",
        height=max(400, len(team_order) * 38 + 150),
    ))
    st.plotly_chart(fig, use_container_width=True)


# Graf 4: K-means clustering

def graf_clustering():
    st.subheader("Grupiranje ekip — K-means clustering")
    st.caption(
        "Ekipe so grupirane glede na povprečno hitrost (MedianPct) in konsistentnost (StdPct). "
        "Ekipe blizu skupaj so si podobne po slogu nastopanja. "
    )

    col1, col2 = st.columns([3, 1])
    with col2:
        n_clusters = st.slider("Število skupin (k)", 2, min(5, len(team_order)), 3,
                               key="kmeans_k")

    features = team_overall[['MedianPct', 'StdPct']].fillna(0)
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    km     = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    team_overall['Cluster'] = labels.astype(str)

    cluster_colors = px.colors.qualitative.Set2[:n_clusters]

    fig = go.Figure()
    for c in sorted(team_overall['Cluster'].unique()):
        sub = team_overall[team_overall['Cluster'] == c]
        ci  = int(c)
        fig.add_trace(go.Scatter(
            x=sub['MedianPct'],
            y=sub['StdPct'],
            mode='markers+text',
            name=f"Skupina {int(c) + 1}",
            text=sub['Team'],
            textposition='top center',
            textfont=dict(size=11, color='white'),
            marker=dict(
                color=cluster_colors[ci],
                size=14,
                line=dict(color='white', width=1),
            ),
            hovertemplate="<b>%{text}</b><br>Mediana: %{x:.3f}%<br>StdDev: %{y:.3f}%<extra></extra>",
        ))

    fig.update_layout(**styled_layout(
        f"K-means clustering ekip — sezona {SEASON}",
        xaxis_title="Povprečna relativna hitrost (MedianPct %)",
        yaxis_title="Nekonsistentnost (StdPct %)",
        legend=dict(bgcolor="rgba(0,0,0,0.2)", font=dict(color="white")),
        height=520,
    ))

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    # Tabela skupin
    st.dataframe(
        team_overall[['Team', 'MedianPct', 'StdPct', 'LapCount', 'Cluster']]
        .rename(columns={
            'Team': 'Ekipa',
            'MedianPct': 'Mediana %',
            'StdPct': 'StdDev %',
            'LapCount': 'Število krogov',
            'Cluster': 'Skupina',
        })
        .sort_values('Mediana %')
        .style.format({'Mediana %': '{:.3f}', 'StdDev %': '{:.3f}'}),
        use_container_width=True,
        hide_index=True,
    )


# Graf 5: Radar chart

def graf_radar():
    st.subheader("Radar chart — primerjava ekip po več dimenzijah")
    st.caption(
        "Primerjava top ekip po petih dimenzijah: povprečna hitrost, konsistentnost, "
        "najboljši krog sezone, trend izboljšanja in število veljavnih krogov."
    )

    # Izračun dimenzij
    team_race_med = (
        laps_teams.groupby(['Team', 'Round'])['LapTimePct']
        .median().reset_index().sort_values('Round')
    )

    radar_rows = []
    for team in team_order:
        d = team_race_med[team_race_med['Team'] == team]
        trend = 0.0
        if len(d) >= 3:
            slope, *_ = stats.linregress(d['Round'], d['LapTimePct'])
            trend = slope  # negativen = izboljšanje

        radar_rows.append({
            'Team':        team,
            'Hitrost':     team_overall.loc[team_overall['Team'] == team, 'MedianPct'].values[0],
            'Konsistentnost': team_overall.loc[team_overall['Team'] == team, 'StdPct'].values[0],
            'BestLap':     laps_teams[laps_teams['Team'] == team]['LapTimePct'].min(),
            'Trend':       trend,
            'Obseg':       team_overall.loc[team_overall['Team'] == team, 'LapCount'].values[0],
        })

    radar_df = pd.DataFrame(radar_rows)

    # Normalizacija: nižje = boljše za vse → invertiramo in skaliramo 0–10
    def norm_invert(series):
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series([5.0] * len(series), index=series.index)
        return 10 - (series - mn) / (mx - mn) * 10

    radar_df['s_Hitrost']        = norm_invert(radar_df['Hitrost'])
    radar_df['s_Konsistentnost'] = norm_invert(radar_df['Konsistentnost'])
    radar_df['s_BestLap']        = norm_invert(radar_df['BestLap'])
    radar_df['s_Trend']          = norm_invert(radar_df['Trend'])
    radar_df['s_Obseg']          = (radar_df['Obseg'] - radar_df['Obseg'].min()) / \
                                    (radar_df['Obseg'].max() - radar_df['Obseg'].min() + 1e-9) * 10

    categories = ['Hitrost', 'Konsistentnost', 'Najboljši krog', 'Trend', 'Obseg podatkov']
    score_cols  = ['s_Hitrost', 's_Konsistentnost', 's_BestLap', 's_Trend', 's_Obseg']

    top_n = st.slider("Število ekip za prikaz", 3, len(team_order), min(6, len(team_order)),
                      key="radar_n")
    selected_teams = team_order[:top_n]

    fig = go.Figure()
    for team in selected_teams:
        row    = radar_df[radar_df['Team'] == team].iloc[0]
        values = [row[c] for c in score_cols]
        values += [values[0]]  # zapri krog
        color  = team_colors.get(team, '#888888')

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            name=team,
            line_color=color,
            fillcolor=color,
            opacity=0.25,
            hovertemplate=f"<b>{team}</b><br>%{{theta}}: %{{r:.2f}}/10<extra></extra>",
        ))

    fig.update_layout(
        **LAYOUT,
        title=dict(
            text=f"Radar chart — top {top_n} ekip, sezona {SEASON}",
            font=dict(color="white", size=15),
        ),
        polar=dict(
            bgcolor="#3B3B3B",
            radialaxis=dict(visible=True, range=[0, 10],
                            gridcolor="#555555", color="#aaaaaa"),
            angularaxis=dict(gridcolor="#555555", color="#aaaaaa"),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0.2)", font=dict(color="white")),
        height=550,
    )
    st.plotly_chart(fig, use_container_width=True)


# Render

graf_violin()
st.divider()
graf_trend_sezone()
st.divider()
graf_heatmap()
st.divider()
graf_clustering()
st.divider()
graf_radar()
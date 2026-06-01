import streamlit as st
import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import logging

logging.getLogger('fastf1').setLevel(logging.ERROR)
cache_path = "./streamlit_app/cache"
os.makedirs(cache_path, exist_ok=True)
fastf1.Cache.enable_cache(cache_path)
fastf1.plotting.setup_mpl(color_scheme='fastf1')

st.title('Vpliv vremenskih razmer')

wet_races = ['Australian Grand Prix', 'British Grand Prix', 'Belgian Grand Prix']

@st.cache_data
def load_data():
    all_laps = []
    schedule = fastf1.get_event_schedule(2025, include_testing=False)
    schedule = schedule[schedule['EventName'].isin(wet_races)]
    for _, event in schedule.iterrows():
        try:
            session = fastf1.get_session(2025, event['RoundNumber'], 'R')
            session.load(telemetry=False, weather=True, messages=False)
            laps = session.laps.copy()
            weather = session.weather_data.copy()
            laps = pd.merge_asof(
                laps.sort_values('LapStartTime'),
                weather.sort_values('Time').rename(columns={'Time': 'LapStartTime'}),
                on='LapStartTime'
            )
            laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
            laps['Round'] = event['RoundNumber']
            laps['EventName'] = event['EventName']
            all_laps.append(laps)
        except:
            pass
    return pd.concat(all_laps, ignore_index=True), session

with st.spinner('Nalagam podatke...'):
    df, session = load_data()


tab1, tab2, tab3 = st.tabs(['Povprečni mokri časi', 'Točke pridobljene na mokrih dirkah', 'Prehod med mokrimi in suhimi'])

with tab1:
    N = 50
    
    wet_laps = df[df['Compound'] == 'INTERMEDIATE']
    wet_lap_counts = wet_laps.groupby('Driver')['LapTimeSeconds'].count()
    valid_drivers = wet_lap_counts[wet_lap_counts >= N].index
    wet_avg = wet_laps[wet_laps['Driver'].isin(valid_drivers)].groupby('Driver')['LapTimeSeconds'].mean().reset_index()
    wet_avg.columns = ['Driver', 'AvgWetLapTime']
    wet_avg = wet_avg.sort_values('AvgWetLapTime')
    
    colors_driver = []
    for driver in wet_avg['Driver']:
        try:
            style = fastf1.plotting.get_driver_style(driver, ['color'], session)
            colors_driver.append(style['color'])
        except:
            colors_driver.append('#808080')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(wet_avg['Driver'], wet_avg['AvgWetLapTime'], color=colors_driver, edgecolor='white')
    ax.set_xlabel('Voznik')
    ax.set_ylabel('Povprečen čas kroga (s)')
    ax.set_title('Povprečen čas kroga v deževnih razmerah')
    ax.set_ylim(wet_avg['AvgWetLapTime'].min() - 1, wet_avg['AvgWetLapTime'].max() + 1)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    wet_race_results = []
    for race_name in wet_races:
        try:
            round_num = df[df['EventName'] == race_name]['Round'].iloc[0]
            session = fastf1.get_session(2025, int(round_num), 'R')
            session.load(telemetry=False, weather=False, messages=False)
            results = session.results[['Abbreviation', 'Points']].copy()
            results['EventName'] = race_name
            wet_race_results.append(results)
        except Exception as e:
            print(f"Skipping {race_name}: {e}")

    wet_results_df = pd.concat(wet_race_results, ignore_index=True)

    wet_points = wet_results_df.groupby('Abbreviation')['Points'].sum().reset_index()
    wet_points.columns = ['Driver', 'TotalPoints']
    wet_points = wet_points.sort_values('TotalPoints', ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))

    colors_driver = []
    for driver in wet_points['Driver']:
        try:
            style = fastf1.plotting.get_driver_style(driver, ['color'], session)
            colors_driver.append(style['color'])
        except:
            colors_driver.append('#808080')

    ax.bar(wet_points['Driver'], wet_points['TotalPoints'], color=colors_driver, edgecolor='white')
    ax.set_xlabel('Voznik')
    ax.set_ylabel('Skupne točke')
    ax.set_title('F1 sezona 2025 - Točke voznikov na mokrih dirkah')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)
    
with tab3:
    race = st.selectbox('Izberi dirko', wet_races)
    
    race_df = df[df['EventName'] == race]
    race_wet = race_df[race_df['Compound'] == 'INTERMEDIATE']
    race_dry = race_df[~race_df['Compound'].isin(['INTERMEDIATE', 'WET'])]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.scatter(race_wet['LapNumber'], race_wet['LapTimeSeconds'],
               alpha=0.5, s=20, color='dodgerblue', label='Intermediate')
    ax.scatter(race_dry['LapNumber'], race_dry['LapTimeSeconds'],
               alpha=0.5, s=20, color='orange', label='Dry')
    ax.set_xlabel('Krog')
    ax.set_ylabel('Čas kroga (s)')
    ax.set_title(f'{race} - Prehod med mokrimi in suhimi razmerami')
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    
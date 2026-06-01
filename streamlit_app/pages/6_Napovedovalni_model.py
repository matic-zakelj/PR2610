import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
import joblib

logging.getLogger('fastf1').setLevel(logging.ERROR)
cache_path = "./streamlit_app/cache"
os.makedirs(cache_path, exist_ok=True)
fastf1.Cache.enable_cache(cache_path)
fastf1.plotting.setup_mpl(color_scheme='fastf1')

model_path = "./model.pkl"
model = joblib.load(model_path)
features = ['GridPosition', 'AvgPos_last5', 'AvgGrid_last5', 'CumPoints']

@st.cache_data
def load_season_data(year, num_rounds):
    all_results = []
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    for _, event in schedule[schedule['RoundNumber'] <= num_rounds].iterrows():
        try:
            session = fastf1.get_session(year, event['RoundNumber'], 'R')
            session.load(telemetry=False, weather=False, messages=False)
            results = session.results[['Abbreviation', 'GridPosition', 'Position', 'Points']].copy()
            results['Year'] = year
            results['Round'] = event['RoundNumber']
            all_results.append(results)
        except:
            pass
    df = pd.concat(all_results, ignore_index=True)
    df['Position'] = pd.to_numeric(df['Position'], errors='coerce')
    df['GridPosition'] = pd.to_numeric(df['GridPosition'], errors='coerce')
    return df.sort_values('Round').reset_index(drop=True)

st.title('F1 Napoved prvaka')
st.subheader('Opozorilo: Model je bil treniran na podatkih 2018-2025, zato so lahko napovedi pristransko natančne za te sezone!!!')

st.header('Nastavitve')
season = st.selectbox('Sezona', [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026])
num_rounds = 5

if st.button('Napovej'):
    with st.spinner('Nalagam podatke sezone...'):
        df_season = load_season_data(season, num_rounds)

    current_state = df_season.groupby('Abbreviation').agg(
        GridPosition=('GridPosition', 'mean'),
        AvgPos_last5=('Position', 'mean'),
        AvgGrid_last5=('GridPosition', 'mean'),
        CumPoints=('Points', 'sum')
    ).reset_index()

    points_system = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    total_rounds = len(schedule)

    all_predictions = []
    current_state = current_state.copy()

    for round_num in range(num_rounds + 1, total_rounds + 1):
        current_state['GridPosition'] = current_state['AvgGrid_last5'].apply(
            lambda x: max(1, min(20, int(np.random.normal(x, 2))))
        )
        current_state['PredictedPosition'] = model.predict(current_state[features])
        current_state = current_state.sort_values('PredictedPosition').reset_index(drop=True)
        current_state['FinalPosition'] = range(1, len(current_state) + 1)
        current_state['RoundPoints'] = current_state['FinalPosition'].map(points_system).fillna(0)

        round_pred = current_state[['Abbreviation', 'FinalPosition', 'RoundPoints']].copy()
        round_pred['Round'] = round_num
        all_predictions.append(round_pred)

        current_state['AvgPos_last5'] = (current_state['AvgPos_last5'] * 4 + current_state['FinalPosition']) / 5
        current_state['AvgGrid_last5'] = (current_state['AvgGrid_last5'] * 4 + current_state['GridPosition']) / 5
        current_state['CumPoints'] = current_state['CumPoints'] + current_state['RoundPoints']

    pred_df = pd.concat(all_predictions, ignore_index=True)

    st.header('Napovedi po dirkah')
    for round_num, race in pred_df.groupby('Round'):
        top3 = race.sort_values('FinalPosition').head(3)['Abbreviation'].tolist()
        event_name = schedule[schedule['RoundNumber'] == round_num]['EventName'].iloc[0]
        st.write(f"**Dirka {round_num} - {event_name}**")
        st.write(f"1. {top3[0]}  \n2. {top3[1]}  \n3. {top3[2]}")

    points_first = df_season.groupby('Abbreviation')['Points'].sum().reset_index()
    points_pred = pred_df.groupby('Abbreviation')['RoundPoints'].sum().reset_index()
    total = points_first.merge(points_pred, on='Abbreviation')
    total['TotalPoints'] = total['Points'] + total['RoundPoints']
    total = total.sort_values('TotalPoints', ascending=False)

    st.header('Napoved prvaka')
    st.write(f"🏆 **{total.iloc[0]['Abbreviation']}** z {int(total.iloc[0]['TotalPoints'])} točkami")

    top10 = total.head(10)['Abbreviation'].tolist()
    first5_rounds = df_season.groupby(['Abbreviation', 'Round'])['Points'].sum().reset_index()
    first5_rounds = first5_rounds[first5_rounds['Abbreviation'].isin(top10)]
    pred_rounds = pred_df[pred_df['Abbreviation'].isin(top10)][['Abbreviation', 'Round', 'RoundPoints']].rename(columns={'RoundPoints': 'Points'})

    all_rounds = pd.concat([first5_rounds, pred_rounds], ignore_index=True)
    all_rounds = all_rounds.sort_values(['Abbreviation', 'Round'])
    all_rounds['CumPoints'] = all_rounds.groupby('Abbreviation')['Points'].cumsum()

    fig, ax = plt.subplots(figsize=(14, 7))
    sample_session = fastf1.get_session(season, 1, 'R')
    sample_session.load(telemetry=False, weather=False, messages=False)
    
    for driver in top10:
        data = all_rounds[all_rounds['Abbreviation'] == driver]
        try:
            style = fastf1.plotting.get_driver_style(driver, ['color', 'linestyle'], sample_session)
            ax.plot(data['Round'], data['CumPoints'], label=driver,
                   color=style['color'], linewidth=2)
        except:
            ax.plot(data['Round'], data['CumPoints'], label=driver, linewidth=2)

    ax.axvline(x=num_rounds + 0.5, color='white', linestyle='--', alpha=0.7, label='Konec znanih dirk')
    ax.set_xlabel('Dirka')
    ax.set_ylabel('Kumulativne točke')
    ax.set_title(f'Napoved prvaka {season}')
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
import streamlit as st

st.title('Interactive Widgets')

name = st.text_input('Enter your name:')
st.write(f'Hello, {name}!')

age = st.slider('Select your age:', 0, 100, 25)
st.write(f'You are {age} years old.')
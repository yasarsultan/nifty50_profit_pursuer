import streamlit as st
import plotly.graph_objects as go
 
fig = go.Figure(data=go.Scatter(x=[1, 2, 3, 4], y=[10, 15, 7, 10]))

st.plotly_chart(fig)

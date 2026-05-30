import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data

st.title("📊 Overview Dashboard")
df = load_data()

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Predicted Volume (L)",
            f"{df['predicted_jan_2026_potential'].sum():,.0f}")
col2.metric("Total Historical Avg (L)",
            f"{df['observed_avg_monthly'].sum():,.0f}")
col3.metric("Avg Lift %",
            f"{df['lift_pct'].mean():.1f}%")
col4.metric("Constrained Outlets",
            f"{df['is_constrained'].sum():,}")

st.markdown("---")

# --- Charts row 1 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Predicted Potential by Province")
    fig = px.bar(
        df.groupby('Province')['predicted_jan_2026_potential']
          .sum().reset_index(),
        x='Province', y='predicted_jan_2026_potential',
        color='Province',
        labels={'predicted_jan_2026_potential': 'Predicted Volume (L)'},
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Outlet Type Distribution")
    fig = px.pie(
        df, names='Outlet_Type',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Charts row 2 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Lift % Distribution")
    fig = px.histogram(
        df, x='lift_pct', nbins=50,
        labels={'lift_pct': 'Lift %'},
        color_discrete_sequence=['#00CC96']
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Top 10 Outlets by Predicted Potential")
    top10 = df.nlargest(10, 'predicted_jan_2026_potential')[
        ['Outlet_ID', 'Outlet_Type', 'Province',
         'predicted_jan_2026_potential', 'lift_pct']
    ]
    st.dataframe(top10, use_container_width=True)
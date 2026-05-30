import streamlit as st

st.set_page_config(
    page_title="Outlet Intelligence Platform",
    page_icon="🥤",
    layout="wide"
)

st.title("🥤 Outlet Intelligence Platform")
st.caption("Data Storm v7.0 — Data Drifters")

from data.loader import load_data
df = load_data()

st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Outlets",        f"{len(df):,}")
col2.metric("Provinces",            df['Province'].nunique())
col3.metric("Distributors",         df['Distributor_ID'].nunique())
col4.metric("Avg Predicted (L)",    f"{df['predicted_jan_2026_potential'].mean():,.0f}")
col5.metric("Western Budget",       "LKR 5,000,000")

st.markdown("---")
st.info("👈 Use the sidebar to navigate between pages")
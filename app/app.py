import streamlit as st

st.set_page_config(
    page_title="Outlet Intelligence Platform",
    page_icon="🥤",
    layout="wide"
)

st.title("🥤 Outlet Intelligence Platform")
st.caption("Data Storm v7.0 — Data Drifters | Powered by Octave · John Keells Group")

from data.loader import load_data
df = load_data()

st.markdown("---")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Outlets",            f"{len(df):,}")
c2.metric("Provinces",                df['Province'].nunique())
c3.metric("Distributors",             df['Distributor_ID'].nunique())
c4.metric("Avg Predicted Jan 2026",   f"{df['predicted_jan_2026_potential'].mean():,.0f} L")
c5.metric("Western Budget",           "LKR 5,000,000")

st.markdown("---")
st.info("👈 Use the sidebar to navigate between pages")
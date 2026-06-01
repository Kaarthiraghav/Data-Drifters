import streamlit as st

st.set_page_config(
    page_title="Outlet Intelligence Platform",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card { background:#f0f2f6; border-radius:8px; padding:12px; text-align:center; }
    .stMetric label { font-size:0.8rem; color:#666; }
    div[data-testid="stSidebarNav"] li div a span { font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

from data.loader import load_data
df = load_data()

st.title("🥤 Outlet Intelligence Platform")
st.caption("Data Storm v7.0 · Data Drifters · Powered by Octave – John Keells Group")
st.markdown("---")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Outlets",            f"{len(df):,}")
c2.metric("Provinces",                df['Province'].nunique())
c3.metric("Distributors",             df['Distributor_ID'].nunique())
c4.metric("Avg Predicted Jan 2026",   f"{df['predicted_jan_2026_potential'].mean():,.0f} L")
c5.metric("Western Province Budget",  "LKR 5,000,000")

st.markdown("---")
st.info("👈 Use the sidebar to navigate between pages")
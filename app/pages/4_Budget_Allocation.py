import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data

st.title("💰 Budget Allocation — Western Province")
df = load_data()

western = df[df['Province'] == 'Western'].copy()
allocated = western[western['trade_spend_lkr'] > 0]

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Budget",       "LKR 5,000,000")
col2.metric("Total Allocated",    f"LKR {allocated['trade_spend_lkr'].sum():,.0f}")
col3.metric("Outlets Receiving Spend", len(allocated))
col4.metric("Remaining Budget",
            f"LKR {5_000_000 - allocated['trade_spend_lkr'].sum():,.0f}")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Spend by Distributor")
    fig = px.bar(
        allocated.groupby('Distributor_ID')['trade_spend_lkr']
                 .sum().reset_index(),
        x='Distributor_ID', y='trade_spend_lkr',
        color='Distributor_ID',
        labels={'trade_spend_lkr': 'Spend (LKR)'}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Spend by Type")
    fig = px.pie(
        allocated, names='spend_type', values='trade_spend_lkr',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Map ---
st.subheader("Spend Map — Western Province")
map_data = allocated.dropna(subset=['Latitude', 'Longitude'])
m = folium.Map(location=[6.9, 79.9], zoom_start=9)

for _, row in map_data.iterrows():
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=max(3, row['trade_spend_lkr'] / 5000),
        color='blue', fill=True, fill_opacity=0.6,
        popup=folium.Popup(
            f"<b>{row['Outlet_ID']}</b><br>"
            f"Spend: LKR {row['trade_spend_lkr']:,.0f}<br>"
            f"Type: {row['spend_type']}<br>"
            f"Predicted: {row['predicted_jan_2026_potential']:.0f}L",
            max_width=200
        )
    ).add_to(m)

st_folium(m, width=900, height=450)

# --- Table ---
st.subheader("Allocation Table")
st.dataframe(
    allocated[[
        'Outlet_ID', 'Outlet_Type', 'Distributor_ID',
        'predicted_jan_2026_potential', 'lift',
        'trade_spend_lkr', 'spend_type'
    ]].sort_values('trade_spend_lkr', ascending=False),
    use_container_width=True
)
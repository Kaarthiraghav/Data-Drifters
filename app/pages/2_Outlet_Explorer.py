import streamlit as st
import folium
from streamlit_folium import st_folium
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data

st.title("🗺️ Outlet Explorer")
df = load_data()

# --- Filters ---
col1, col2, col3 = st.columns(3)

province    = col1.selectbox("Province",     ["All"] + sorted(df['Province'].unique().tolist()))
distributor = col2.selectbox("Distributor",  ["All"] + sorted(df['Distributor_ID'].unique().tolist()))
otype       = col3.selectbox("Outlet Type",  ["All"] + sorted(df['Outlet_Type'].unique().tolist()))

filtered = df.copy()
if province    != "All": filtered = filtered[filtered['Province']      == province]
if distributor != "All": filtered = filtered[filtered['Distributor_ID']== distributor]
if otype       != "All": filtered = filtered[filtered['Outlet_Type']   == otype]

st.caption(f"Showing {len(filtered):,} outlets")

# --- Map ---
map_data = filtered.dropna(subset=['Latitude', 'Longitude'])

m = folium.Map(location=[7.8731, 80.7718], zoom_start=7)

for _, row in map_data.iterrows():
    color = (
        'green'  if row['lift_pct'] > 80 else
        'orange' if row['lift_pct'] > 40 else
        'red'
    )
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=4,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(
            f"<b>{row['Outlet_ID']}</b><br>"
            f"Type: {row['Outlet_Type']}<br>"
            f"Predicted: {row['predicted_jan_2026_potential']:.0f}L<br>"
            f"Lift: {row['lift_pct']:.1f}%",
            max_width=200
        )
    ).add_to(m)

st_folium(m, width=900, height=500)

st.caption("🟢 High lift (>80%)  🟠 Medium lift (40–80%)  🔴 Low lift (<40%)")

# --- Table ---
st.subheader("Outlet Table")
st.dataframe(
    filtered[[
        'Outlet_ID', 'Outlet_Type', 'Province', 'Distributor_ID',
        'observed_avg_monthly', 'predicted_jan_2026_potential',
        'lift', 'lift_pct', 'is_constrained'
    ]].sort_values('lift_pct', ascending=False),
    use_container_width=True
)
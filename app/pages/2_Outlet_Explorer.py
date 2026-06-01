import streamlit as st
import folium
from streamlit_folium import st_folium
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data

st.title("🗺️ Outlet Explorer")
df = load_data()

# ── Filters ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

province = c1.selectbox("Province", ["All"] + sorted(df['Province'].unique().tolist()))

avail_dist = sorted(
    df[df['Province'] == province]['Distributor_ID'].unique().tolist()
    if province != "All" else df['Distributor_ID'].unique().tolist()
)
distributor = c2.selectbox("Distributor", ["All"] + avail_dist)

otype = c3.selectbox("Outlet Type", ["All"] + sorted(df['Outlet_Type'].unique().tolist()))

constrained = c4.selectbox("Constrained?", ["All", "Yes", "No"])

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df.copy()
if province     != "All": filtered = filtered[filtered['Province']       == province]
if distributor  != "All": filtered = filtered[filtered['Distributor_ID'] == distributor]
if otype        != "All": filtered = filtered[filtered['Outlet_Type']    == otype]
if constrained  == "Yes": filtered = filtered[filtered['is_constrained'] == 1]
if constrained  == "No":  filtered = filtered[filtered['is_constrained'] == 0]

# ── Summary bar ───────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Outlets Shown",    f"{len(filtered):,}")
c2.metric("Avg Predicted (L)",f"{filtered['predicted_jan_2026_potential'].mean():,.0f}")
c3.metric("Avg Historical (L)",f"{filtered['observed_avg_monthly'].mean():,.0f}")
c4.metric("Avg Uplift %",     f"{filtered['lift_pct'].mean():.1f}%")

# ── Map ───────────────────────────────────────────────────────────────────────
st.subheader("Outlet Map")
map_data = filtered.dropna(subset=['Latitude','Longitude']).head(5000)

center_lat = map_data['Latitude'].mean() if len(map_data) else 7.87
center_lon = map_data['Longitude'].mean() if len(map_data) else 80.77

m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

for _, row in map_data.iterrows():
    color = 'green' if row['lift_pct'] > 80 else 'orange' if row['lift_pct'] > 40 else 'red'
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=4,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(
            f"<b>{row['Outlet_ID']}</b><br>"
            f"Type: {row['Outlet_Type']} ({row['Outlet_Size']})<br>"
            f"Distributor: {row['Distributor_ID']}<br>"
            f"Predicted: <b>{row['predicted_jan_2026_potential']:.0f} L</b><br>"
            f"Historical: {row['observed_avg_monthly']:.0f} L<br>"
            f"Uplift: <b>{row['lift_pct']:.1f}%</b><br>"
            f"Constrained: {'⚠️ Yes' if row['is_constrained'] else '✅ No'}",
            max_width=230
        )
    ).add_to(m)

st_folium(m, width=900, height=500)
st.caption("🟢 High uplift (>80%)  🟠 Medium (40–80%)  🔴 Low (<40%)  — Click any outlet for details")

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Outlet Table")
st.dataframe(
    filtered[[
        'Outlet_ID','Outlet_Type','Outlet_Size','Province',
        'Distributor_ID','observed_avg_monthly',
        'predicted_jan_2026_potential','lift','lift_pct','is_constrained'
    ]].rename(columns={
        'observed_avg_monthly':        'Historical (L)',
        'predicted_jan_2026_potential':'Predicted (L)',
        'lift':                        'Lift (L)',
        'lift_pct':                    'Uplift %',
        'is_constrained':              'Constrained'
    }).sort_values('Uplift %', ascending=False),
    use_container_width=True
)
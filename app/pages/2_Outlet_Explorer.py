import streamlit as st
import folium
from streamlit_folium import st_folium
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data

st.title("🗺️ Outlet Explorer")
df = load_data()

# ── Filters ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

province = c1.selectbox("Province", ["All"] + sorted(df['Province'].unique().tolist()))

# Distributors filtered by province
if province != "All":
    avail_dist = sorted(df[df['Province'] == province]['Distributor_ID'].unique().tolist())
else:
    avail_dist = sorted(df['Distributor_ID'].unique().tolist())
distributor = c2.selectbox("Distributor", ["All"] + avail_dist)

otype = c3.selectbox("Outlet Type", ["All"] + sorted(df['Outlet_Type'].unique().tolist()))

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df.copy()
if province    != "All": filtered = filtered[filtered['Province']       == province]
if distributor != "All": filtered = filtered[filtered['Distributor_ID'] == distributor]
if otype       != "All": filtered = filtered[filtered['Outlet_Type']    == otype]

st.caption(f"Showing **{len(filtered):,}** outlets  |  "
           f"Avg predicted: **{filtered['predicted_jan_2026_potential'].mean():,.0f} L**  |  "
           f"Avg uplift: **{filtered['lift_pct'].mean():.1f}%**")

# ── Map ───────────────────────────────────────────────────────────────────────
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
            f"Distributor: {row['Distributor_ID']}<br>"
            f"Predicted: {row['predicted_jan_2026_potential']:.0f} L<br>"
            f"Historical: {row['observed_avg_monthly']:.0f} L<br>"
            f"Uplift: {row['lift_pct']:.1f}%<br>"
            f"Constrained: {'Yes ⚠️' if row['is_constrained'] else 'No'}",
            max_width=220
        )
    ).add_to(m)

st_folium(m, width=900, height=500)
st.caption("🟢 High uplift (>80%)  🟠 Medium (40–80%)  🔴 Low (<40%)")

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Outlet Table")
st.dataframe(
    filtered[[
        'Outlet_ID', 'Outlet_Type', 'Outlet_Size', 'Province',
        'Distributor_ID', 'observed_avg_monthly',
        'predicted_jan_2026_potential', 'lift', 'lift_pct', 'is_constrained'
    ]].rename(columns={
        'observed_avg_monthly': 'Historical Avg (L)',
        'predicted_jan_2026_potential': 'Predicted (L)',
        'lift': 'Lift (L)',
        'lift_pct': 'Uplift %',
        'is_constrained': 'Constrained'
    }).sort_values('Uplift %', ascending=False),
    use_container_width=True
)
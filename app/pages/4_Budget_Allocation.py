import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data

st.title("💰 Budget Allocation — Western Province")
df = load_data()

western  = df[df['Province'] == 'Western'].copy()
allocated = western[western['Trade_Spend_Allocation_LKR'] > 0]
total_allocated = allocated['Trade_Spend_Allocation_LKR'].sum()
BUDGET = 5_000_000

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Budget",              "LKR 5,000,000")
c2.metric("Total Allocated",           f"LKR {total_allocated:,.0f}")
c3.metric("Outlets Receiving Spend",   f"{len(allocated):,}")
c4.metric("Remaining",                 f"LKR {BUDGET - total_allocated:,.0f}")

# Budget utilisation bar
pct = min(total_allocated / BUDGET * 100, 100)
st.markdown(f"**Budget Utilisation: {pct:.1f}%**")
st.progress(pct / 100)

st.markdown("---")

# ── Charts ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Spend by Distributor")
    dist_spend = (
        allocated.groupby('Distributor_ID')['Trade_Spend_Allocation_LKR']
        .sum().reset_index()
        .sort_values('Trade_Spend_Allocation_LKR', ascending=False)
    )
    fig = px.bar(
        dist_spend, x='Distributor_ID', y='Trade_Spend_Allocation_LKR',
        color='Distributor_ID',
        labels={'Trade_Spend_Allocation_LKR': 'Spend (LKR)'},
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Spend vs Predicted Uplift")
    fig = px.scatter(
        allocated,
        x='Trade_Spend_Allocation_LKR',
        y='lift',
        color='Distributor_ID',
        hover_data=['Outlet_ID', 'Outlet_Type'],
        labels={
            'Trade_Spend_Allocation_LKR': 'Trade Spend (LKR)',
            'lift': 'Predicted Lift (L)'
        },
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Tier breakdown ────────────────────────────────────────────────────────────
st.subheader("Allocation Tier Breakdown")
c1, c2, c3 = st.columns(3)

tier1 = allocated[allocated['Trade_Spend_Allocation_LKR'] >= 100_000]
tier2 = allocated[(allocated['Trade_Spend_Allocation_LKR'] >= 50_000) &
                  (allocated['Trade_Spend_Allocation_LKR'] < 100_000)]
tier3 = allocated[allocated['Trade_Spend_Allocation_LKR'] < 50_000]

c1.metric("Tier 1 (≥ LKR 100K)", f"{len(tier1)} outlets",
          f"LKR {tier1['Trade_Spend_Allocation_LKR'].sum():,.0f}")
c2.metric("Tier 2 (50K–100K)",   f"{len(tier2)} outlets",
          f"LKR {tier2['Trade_Spend_Allocation_LKR'].sum():,.0f}")
c3.metric("Tier 3 (< LKR 50K)",  f"{len(tier3)} outlets",
          f"LKR {tier3['Trade_Spend_Allocation_LKR'].sum():,.0f}")

st.markdown("---")

# ── Map ───────────────────────────────────────────────────────────────────────
st.subheader("Spend Map — Western Province")
map_data = allocated.dropna(subset=['Latitude', 'Longitude'])

m = folium.Map(location=[6.9, 79.9], zoom_start=9)

for _, row in map_data.iterrows():
    radius = max(4, row['Trade_Spend_Allocation_LKR'] / 8000)
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=radius,
        color='#1f77b4',
        fill=True,
        fill_opacity=0.6,
        popup=folium.Popup(
            f"<b>{row['Outlet_ID']}</b><br>"
            f"Type: {row['Outlet_Type']}<br>"
            f"Distributor: {row['Distributor_ID']}<br>"
            f"Spend: LKR {row['Trade_Spend_Allocation_LKR']:,.0f}<br>"
            f"Predicted: {row['predicted_jan_2026_potential']:.0f} L<br>"
            f"Lift: {row['lift']:.0f} L ({row['lift_pct']:.1f}%)",
            max_width=220
        )
    ).add_to(m)

st_folium(m, width=900, height=450)
st.caption("Bubble size = spend amount")

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Allocation Table")
st.dataframe(
    allocated[[
        'Outlet_ID', 'Outlet_Type', 'Outlet_Size', 'Distributor_ID',
        'observed_avg_monthly', 'predicted_jan_2026_potential',
        'lift', 'lift_pct', 'Trade_Spend_Allocation_LKR', 'is_constrained'
    ]].rename(columns={
        'observed_avg_monthly': 'Historical (L)',
        'predicted_jan_2026_potential': 'Predicted (L)',
        'lift': 'Lift (L)',
        'lift_pct': 'Uplift %',
        'Trade_Spend_Allocation_LKR': 'Spend (LKR)',
        'is_constrained': 'Constrained'
    }).sort_values('Spend (LKR)', ascending=False),
    use_container_width=True
)
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

western   = df[df['Province'] == 'Western'].copy()
allocated = western[western['Trade_Spend_Allocation_LKR'] > 0].copy()
BUDGET    = 5_000_000
total_alloc = allocated['Trade_Spend_Allocation_LKR'].sum()

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Budget",             "LKR 5,000,000")
c2.metric("Total Allocated",          f"LKR {total_alloc:,.0f}")
c3.metric("Remaining",                f"LKR {BUDGET - total_alloc:,.0f}")
c4.metric("Outlets Receiving Spend",  f"{len(allocated):,}")
c5.metric("Avg Spend per Outlet",     f"LKR {total_alloc/max(len(allocated),1):,.0f}")

pct = min(total_alloc / BUDGET * 100, 100)
st.markdown(f"**Budget Utilisation: {pct:.1f}%**")
st.progress(pct / 100)

st.markdown("---")

# ── Tier breakdown ────────────────────────────────────────────────────────────
st.subheader("Allocation Tiers")
c1, c2, c3 = st.columns(3)
t1 = allocated[allocated['Trade_Spend_Allocation_LKR'] >= 100_000]
t2 = allocated[(allocated['Trade_Spend_Allocation_LKR'] >= 50_000) &
               (allocated['Trade_Spend_Allocation_LKR'] <  100_000)]
t3 = allocated[allocated['Trade_Spend_Allocation_LKR'] <   50_000]

c1.metric("🥇 Tier 1 — High Priority (≥ LKR 100K)",
          f"{len(t1)} outlets", f"LKR {t1['Trade_Spend_Allocation_LKR'].sum():,.0f}")
c2.metric("🥈 Tier 2 — Medium (LKR 50K–100K)",
          f"{len(t2)} outlets", f"LKR {t2['Trade_Spend_Allocation_LKR'].sum():,.0f}")
c3.metric("🥉 Tier 3 — Support (< LKR 50K)",
          f"{len(t3)} outlets", f"LKR {t3['Trade_Spend_Allocation_LKR'].sum():,.0f}")

st.markdown("---")

# ── Charts ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Spend by Distributor")
    dist_spend = (
        allocated.groupby('Distributor_ID')['Trade_Spend_Allocation_LKR']
        .agg(['sum','mean','count']).reset_index()
        .rename(columns={'sum':'Total','mean':'Avg','count':'Outlets'})
        .sort_values('Total', ascending=False)
    )
    fig = px.bar(dist_spend, x='Distributor_ID', y='Total',
                 color='Distributor_ID',
                 labels={'Total': 'Total Spend (LKR)'},
                 color_discrete_sequence=px.colors.qualitative.Set2,
                 text='Outlets')
    fig.update_layout(showlegend=False, height=320)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Spend vs Predicted Uplift")
    fig = px.scatter(allocated,
                     x='Trade_Spend_Allocation_LKR',
                     y='lift',
                     color='Distributor_ID',
                     size='predicted_jan_2026_potential',
                     hover_data=['Outlet_ID','Outlet_Type'],
                     labels={
                         'Trade_Spend_Allocation_LKR': 'Trade Spend (LKR)',
                         'lift': 'Predicted Lift (L)'
                     })
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2 charts ──────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Outlet Type Receiving Spend")
    type_spend = allocated.groupby('Outlet_Type')['Trade_Spend_Allocation_LKR'].sum().reset_index()
    fig = px.pie(type_spend, names='Outlet_Type', values='Trade_Spend_Allocation_LKR',
                 color_discrete_sequence=px.colors.qualitative.Pastel, hole=0.35)
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Constrained vs Unconstrained Spend")
    con_spend = allocated.groupby('is_constrained')['Trade_Spend_Allocation_LKR'].sum().reset_index()
    con_spend['Label'] = con_spend['is_constrained'].map({0:'Unconstrained', 1:'Constrained'})
    fig = px.bar(con_spend, x='Label', y='Trade_Spend_Allocation_LKR',
                 color='Label',
                 labels={'Trade_Spend_Allocation_LKR':'Spend (LKR)'},
                 color_discrete_map={'Constrained':'#EF553B','Unconstrained':'#00CC96'})
    fig.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Map ───────────────────────────────────────────────────────────────────────
st.subheader("🗺️ Spend Map — Western Province")
map_data = allocated.dropna(subset=['Latitude','Longitude'])
m = folium.Map(location=[6.9, 79.9], zoom_start=9)

for _, row in map_data.iterrows():
    radius = max(4, row['Trade_Spend_Allocation_LKR'] / 8000)
    color  = 'red' if row['Trade_Spend_Allocation_LKR'] >= 100_000 else \
             'orange' if row['Trade_Spend_Allocation_LKR'] >= 50_000 else 'blue'
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=radius,
        color=color,
        fill=True,
        fill_opacity=0.65,
        popup=folium.Popup(
            f"<b>{row['Outlet_ID']}</b><br>"
            f"Type: {row['Outlet_Type']}<br>"
            f"Distributor: {row['Distributor_ID']}<br>"
            f"<b>Spend: LKR {row['Trade_Spend_Allocation_LKR']:,.0f}</b><br>"
            f"Predicted: {row['predicted_jan_2026_potential']:.0f} L<br>"
            f"Lift: {row['lift']:.0f} L ({row['lift_pct']:.1f}%)<br>"
            f"Constrained: {'⚠️ Yes' if row['is_constrained'] else '✅ No'}",
            max_width=230
        )
    ).add_to(m)

st_folium(m, width=900, height=450)
st.caption("🔴 Tier 1 (≥ LKR 100K)  🟠 Tier 2 (50K–100K)  🔵 Tier 3 (< 50K)  — Bubble size = spend amount")

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Full Allocation Table")
st.dataframe(
    allocated[[
        'Outlet_ID','Outlet_Type','Outlet_Size','Distributor_ID',
        'observed_avg_monthly','predicted_jan_2026_potential',
        'lift','lift_pct','Trade_Spend_Allocation_LKR','is_constrained'
    ]].rename(columns={
        'observed_avg_monthly':        'Historical (L)',
        'predicted_jan_2026_potential':'Predicted (L)',
        'lift':                        'Lift (L)',
        'lift_pct':                    'Uplift %',
        'Trade_Spend_Allocation_LKR':  'Spend (LKR)',
        'is_constrained':              'Constrained'
    }).sort_values('Spend (LKR)', ascending=False),
    use_container_width=True
)
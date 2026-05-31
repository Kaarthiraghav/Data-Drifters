import streamlit as st
import plotly.express as px
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data

st.title("📊 Overview Dashboard")
df = load_data()

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Predicted Volume (L)",  f"{df['predicted_jan_2026_potential'].sum():,.0f}")
c2.metric("Total Historical Avg (L)",    f"{df['observed_avg_monthly'].sum():,.0f}")
c3.metric("Avg Uplift %",                f"{df['lift_pct'].mean():.1f}%")
c4.metric("Constrained Outlets",         f"{int(df['is_constrained'].sum()):,}")

st.markdown("---")

# ── Row 1 ─────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Predicted Potential by Province")
    prov = df.groupby('Province')['predicted_jan_2026_potential'].sum().reset_index()
    fig = px.bar(prov, x='Province', y='predicted_jan_2026_potential',
                 color='Province',
                 labels={'predicted_jan_2026_potential': 'Predicted Volume (L)'},
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Outlet Type Distribution")
    fig = px.pie(df, names='Outlet_Type',
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2 ─────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Uplift % Distribution")
    fig = px.histogram(df, x='lift_pct', nbins=60,
                       labels={'lift_pct': 'Uplift %'},
                       color_discrete_sequence=['#00CC96'])
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Predicted vs Historical by Outlet Size")
    size_df = df.groupby('Outlet_Size').agg(
        Historical=('observed_avg_monthly', 'mean'),
        Predicted=('predicted_jan_2026_potential', 'mean')
    ).reset_index()
    fig = px.bar(size_df.melt(id_vars='Outlet_Size', var_name='Type', value_name='Volume'),
                 x='Outlet_Size', y='Volume', color='Type', barmode='group',
                 labels={'Volume': 'Avg Volume (L)'},
                 color_discrete_sequence=['#636EFA', '#00CC96'])
    st.plotly_chart(fig, use_container_width=True)

# ── Top 10 table ──────────────────────────────────────────────────────────────
st.subheader("🏆 Top 10 Outlets by Predicted Potential")
top10 = df.nlargest(10, 'predicted_jan_2026_potential')[[
    'Outlet_ID', 'Outlet_Type', 'Outlet_Size', 'Province',
    'Distributor_ID', 'observed_avg_monthly',
    'predicted_jan_2026_potential', 'lift_pct', 'is_constrained'
]].rename(columns={
    'observed_avg_monthly': 'Historical Avg (L)',
    'predicted_jan_2026_potential': 'Predicted (L)',
    'lift_pct': 'Uplift %',
    'is_constrained': 'Constrained'
})
st.dataframe(top10, use_container_width=True)
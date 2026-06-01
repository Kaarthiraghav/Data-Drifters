import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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
c4.metric("Supply-Constrained Outlets",  f"{int(df['is_constrained'].sum()):,}")

st.markdown("---")

# ── Row 1 ─────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Predicted Potential by Province")
    prov = df.groupby('Province')['predicted_jan_2026_potential'].sum().reset_index()
    prov = prov.sort_values('predicted_jan_2026_potential', ascending=False)
    fig = px.bar(prov, x='Province', y='predicted_jan_2026_potential',
                 color='Province',
                 labels={'predicted_jan_2026_potential': 'Predicted Volume (L)'},
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(showlegend=False, height=320)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Outlet Type Distribution")
    fig = px.pie(df, names='Outlet_Type',
                 color_discrete_sequence=px.colors.qualitative.Pastel,
                 hole=0.35)
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2 ─────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Uplift % Distribution")
    fig = px.histogram(df, x='lift_pct', nbins=60,
                       labels={'lift_pct': 'Uplift %'},
                       color_discrete_sequence=['#00CC96'])
    fig.update_layout(showlegend=False, height=320)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Historical vs Predicted by Outlet Size")
    size_df = df.groupby('Outlet_Size').agg(
        Historical=('observed_avg_monthly', 'mean'),
        Predicted=('predicted_jan_2026_potential', 'mean')
    ).reset_index()
    melted = size_df.melt(id_vars='Outlet_Size', var_name='Type', value_name='Volume')
    fig = px.bar(melted, x='Outlet_Size', y='Volume', color='Type', barmode='group',
                 labels={'Volume': 'Avg Volume (L)'},
                 color_discrete_sequence=['#636EFA', '#00CC96'])
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True)

# ── Row 3: constrained vs unconstrained ──────────────────────────────────────
st.subheader("Constrained vs Unconstrained — Potential Gap")
c1, c2 = st.columns(2)

with c1:
    fig = px.box(df, x='is_constrained', y='lift_pct',
                 labels={'is_constrained': 'Supply Constrained', 'lift_pct': 'Uplift %'},
                 color='is_constrained',
                 color_discrete_map={0: '#00CC96', 1: '#EF553B'})
    fig.update_xaxes(tickvals=[0,1], ticktext=['No','Yes'])
    fig.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.scatter(df.sample(min(2000, len(df))),
                     x='observed_avg_monthly',
                     y='predicted_jan_2026_potential',
                     color='Province',
                     opacity=0.4, size_max=4,
                     labels={
                         'observed_avg_monthly': 'Historical Avg (L)',
                         'predicted_jan_2026_potential': 'Predicted Jan 2026 (L)'
                     })
    fig.add_shape(type='line', x0=0, y0=0,
                  x1=df['observed_avg_monthly'].max(),
                  y1=df['observed_avg_monthly'].max(),
                  line=dict(dash='dash', color='gray'))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

# ── Top 10 ─────────────────────────────────────────────────────────────────────
st.subheader("🏆 Top 10 Outlets by Predicted Potential")
top10 = df.nlargest(10, 'predicted_jan_2026_potential')[[
    'Outlet_ID','Outlet_Type','Outlet_Size','Province',
    'Distributor_ID','observed_avg_monthly',
    'predicted_jan_2026_potential','lift_pct','is_constrained'
]].rename(columns={
    'observed_avg_monthly':        'Historical Avg (L)',
    'predicted_jan_2026_potential':'Predicted (L)',
    'lift_pct':                    'Uplift %',
    'is_constrained':              'Constrained'
})
st.dataframe(top10, use_container_width=True)
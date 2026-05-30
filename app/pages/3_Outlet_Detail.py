import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data

st.title("🔍 Outlet Detail")
df = load_data()

# --- Search ---
outlet_id = st.selectbox("Select Outlet", df['Outlet_ID'].tolist())
row = df[df['Outlet_ID'] == outlet_id].iloc[0]

st.markdown("---")

# --- Top KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Outlet Type",       row['Outlet_Type'])
col2.metric("Province",          row['Province'])
col3.metric("Distributor",       row['Distributor_ID'])
col4.metric("Constrained?",      "Yes ⚠️" if row['is_constrained'] else "No ✅")

st.markdown("---")

# --- Volume comparison ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Volume Comparison")
    fig = go.Figure()
    fig.add_bar(
        x=['Historical Avg', 'Observed Max', 'Predicted Jan 2026'],
        y=[
            row['observed_avg_monthly'],
            row['observed_max_monthly'],
            row['predicted_jan_2026_potential']
        ],
        marker_color=['#636EFA', '#EF553B', '#00CC96']
    )
    fig.update_layout(yaxis_title="Volume (Liters)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Key Metrics")
    st.metric("Historical Avg (L)",   f"{row['observed_avg_monthly']:.1f}")
    st.metric("Observed Max (L)",     f"{row['observed_max_monthly']:.1f}")
    st.metric("Predicted Jan 2026 (L)", f"{row['predicted_jan_2026_potential']:.1f}")
    st.metric("Lift",                 f"{row['lift']:.1f}L  ({row['lift_pct']:.1f}%)")
    st.metric("Cooler Count",         int(row['Cooler_Count']))
    st.metric("Outlet Size",          row['Outlet_Size'])

st.markdown("---")

# --- SHAP Feature Importance ---
st.subheader("🧠 Top Factors Driving This Score")
features = [row['shap_feature_1'], row['shap_feature_2'], row['shap_feature_3']]
values   = [row['shap_value_1'],   row['shap_value_2'],   row['shap_value_3']]
colors   = ['green' if v > 0 else 'red' for v in values]

fig = go.Figure(go.Bar(
    x=values, y=features,
    orientation='h',
    marker_color=colors
))
fig.update_layout(
    xaxis_title="SHAP Impact",
    yaxis_title="Feature",
    height=250
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- LLM Explanation ---
st.subheader("💬 AI Explanation")
st.info(row['llm_explanation'])

# --- Budget allocation if Western ---
if row['Province'] == 'Western' and row['trade_spend_lkr'] > 0:
    st.markdown("---")
    st.subheader("💰 Budget Allocation")
    col1, col2 = st.columns(2)
    col1.metric("Trade Spend Allocated", f"LKR {row['trade_spend_lkr']:,.0f}")
    col2.metric("Spend Type", row['spend_type'].replace('_', ' ').title())
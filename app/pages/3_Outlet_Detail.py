import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data, load_transactions

st.title("🔍 Outlet Detail")
df = load_data()

# ── Search ────────────────────────────────────────────────────────────────────
outlet_id = st.selectbox("Search Outlet ID", df['Outlet_ID'].tolist())
row = df[df['Outlet_ID'] == outlet_id].iloc[0]

st.markdown("---")

# ── Header KPIs ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Outlet Type",  row['Outlet_Type'])
c2.metric("Outlet Size",  row['Outlet_Size'])
c3.metric("Province",     row['Province'])
c4.metric("Distributor",  row['Distributor_ID'])
c5.metric("Constrained?", "Yes ⚠️" if row['is_constrained'] else "No ✅")

st.markdown("---")

# ── Volume comparison + metrics ───────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Volume Comparison")
    fig = go.Figure()
    fig.add_bar(
        x=['Historical Avg', 'Observed Max', 'Predicted Jan 2026'],
        y=[
            row['observed_avg_monthly'],
            row['observed_max_monthly'],
            row['predicted_jan_2026_potential']
        ],
        marker_color=['#636EFA', '#EF553B', '#00CC96'],
        text=[
            f"{row['observed_avg_monthly']:.0f}L",
            f"{row['observed_max_monthly']:.0f}L",
            f"{row['predicted_jan_2026_potential']:.0f}L"
        ],
        textposition='outside'
    )
    fig.update_layout(yaxis_title="Volume (Liters)", showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Key Metrics")
    st.metric("Historical Avg (L)",      f"{row['observed_avg_monthly']:.1f}")
    st.metric("Observed Max (L)",        f"{row['observed_max_monthly']:.1f}")
    st.metric("Predicted Jan 2026 (L)",  f"{row['predicted_jan_2026_potential']:.1f}")
    st.metric("Lift",                    f"{row['lift']:.1f} L  ({row['lift_pct']:.1f}%)")
    st.metric("Cooler Count",            int(row['Cooler_Count']))
    st.metric("Jan Seasonality Score",   f"{row['jan_seasonality_score']:.2f}")

st.markdown("---")

# ── SHAP feature importance ───────────────────────────────────────────────────
st.subheader("🧠 Top Factors Driving This Score")

features = [row['shap_feature_1'], row['shap_feature_2'], row['shap_feature_3']]
values   = [row['shap_value_1'],   row['shap_value_2'],   row['shap_value_3']]
colors   = ['#00CC96' if v > 0 else '#EF553B' for v in values]

fig = go.Figure(go.Bar(
    x=values,
    y=[f.replace('_', ' ').title() for f in features],
    orientation='h',
    marker_color=colors,
    text=[f"{v:+.3f}" for v in values],
    textposition='outside'
))
fig.update_layout(
    xaxis_title="SHAP Impact on Prediction",
    height=220,
    margin=dict(l=10, r=10, t=10, b=10)
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── AI Explanation ────────────────────────────────────────────────────────────
st.subheader("💬 AI Explanation")

# Show pre-generated explanation if available
if row['ai_explanation'] and row['ai_explanation'] != 'Explanation unavailable':
    st.info(row['ai_explanation'])

# Live generation button for demo
API_KEY = os.environ.get("OPENROUTER_API_KEY", None)

if API_KEY:
    if st.button("🔄 Generate Fresh AI Explanation", type="primary"):
        with st.spinner("Generating explanation via Gemma 3..."):
            try:
                lift_pct = row['lift_pct']
                prompt = f"""You are a beverage trade marketing analyst in Sri Lanka.
Explain this outlet's sales potential score to a non-technical Sales Manager in 3-4 sentences.

OUTLET DATA:
- Outlet: {outlet_id} ({row['Outlet_Type']}, {row['Outlet_Size']})
- Distributor: {row['Distributor_ID']} | Province: {row['Province']}
- Cooler Units: {int(row['Cooler_Count'])}
- Historical average sales: {row['observed_avg_monthly']:.0f} L/month
- Historical max sales: {row['observed_max_monthly']:.0f} L/month
- Predicted January 2026 Potential: {row['predicted_jan_2026_potential']:.0f} L/month
- Uplift factor: {row['predicted_jan_2026_potential'] / max(row['observed_avg_monthly'], 1):.2f}x above average
- Supply-constrained outlet: {bool(row['is_constrained'])}
- January seasonality score: {row['jan_seasonality_score']:.2f}
- Sales growth trend: {row['growth_ratio']:.3f}
- Competitor density score: {row.get('competitor_density', 0):.3f}
- POI relative density: {row.get('poi_relative_density', 0):.3f}

TOP FACTORS INCREASING PREDICTION:
- {features[0].replace('_',' ').title()}: impact {values[0]:+.3f}
- {features[1].replace('_',' ').title()}: impact {values[1]:+.3f}

TOP FACTOR DECREASING PREDICTION:
- {features[2].replace('_',' ').title()}: impact {values[2]:+.3f}

{'Budget allocated: LKR ' + f"{row['Trade_Spend_Allocation_LKR']:,.0f}" if row.get('Trade_Spend_Allocation_LKR', 0) > 0 else ''}

Write 3-4 sentences explaining:
1. Why this outlet got this score
2. What the key opportunity is
3. What the sales team should do next
Use plain English. No jargon. Be specific."""

                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "meta-llama/llama-3.1-8b-instruct:free",
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    live_explanation = response.json()['choices'][0]['message']['content']
                    st.success("✅ Live explanation generated")
                    st.info(live_explanation)
                else:
                    st.error(f"API error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"Error generating explanation: {e}")
else:
    st.caption("Set OPENROUTER_API_KEY environment variable to enable live AI explanations.")

# ── Budget allocation (Western only) ─────────────────────────────────────────
if row['Province'] == 'Western':
    st.markdown("---")
    st.subheader("💰 Budget Allocation")
    spend = row.get('Trade_Spend_Allocation_LKR', 0)
    if spend > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("Trade Spend Allocated",   f"LKR {spend:,.0f}")
        c2.metric("Est. Volume Uplift",
                  f"{spend / 1000 * 0.01 * row['predicted_jan_2026_potential']:.0f} L")
        c3.metric("ROI",
                  f"{row['predicted_jan_2026_potential'] / max(spend / 1000, 1):.1f} L per LKR 1K")
    else:
        st.info("This outlet was not selected for trade spend in the current allocation.")

# ── Monthly sales history ─────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📈 Sales History")
try:
    tx = load_transactions()
    outlet_tx = tx[tx['Outlet_ID'] == outlet_id].copy()
    if len(outlet_tx) > 0:
        monthly = (
            outlet_tx.groupby(['Year', 'Month'])['Volume_Liters']
            .sum().reset_index()
        )
        monthly['Period'] = (
            monthly['Year'].astype(str) + '-' +
            monthly['Month'].astype(str).str.zfill(2)
        )
        monthly = monthly.sort_values('Period')

        fig = go.Figure()
        fig.add_scatter(
            x=monthly['Period'],
            y=monthly['Volume_Liters'],
            mode='lines+markers',
            line=dict(color='#636EFA', width=2),
            name='Actual Volume'
        )
        fig.add_hline(
            y=row['predicted_jan_2026_potential'],
            line_dash='dash',
            line_color='#00CC96',
            annotation_text=f"Predicted Potential: {row['predicted_jan_2026_potential']:.0f}L"
        )
        fig.add_hline(
            y=row['observed_avg_monthly'],
            line_dash='dot',
            line_color='#EF553B',
            annotation_text=f"Historical Avg: {row['observed_avg_monthly']:.0f}L"
        )
        fig.update_layout(
            yaxis_title="Volume (L)",
            xaxis_title="Month",
            height=320,
            xaxis_tickangle=-45,
            legend=dict(orientation='h')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transaction history found for this outlet.")
except Exception:
    st.info("Transaction history not available.")

# ── Location map ──────────────────────────────────────────────────────────────
import pandas as pd
if not pd.isna(row['Latitude']) and not pd.isna(row['Longitude']):
    st.markdown("---")
    st.subheader("📍 Location")
    m = folium.Map(location=[row['Latitude'], row['Longitude']], zoom_start=14)
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=f"{outlet_id} — {row['Outlet_Type']} ({row['Province']})",
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)
    st_folium(m, width=700, height=300)
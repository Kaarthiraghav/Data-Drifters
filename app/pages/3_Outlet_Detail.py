import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests, os, pandas as pd
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.loader import load_data, load_transactions

st.title("🔍 Outlet Detail")
df = load_data()

# ── Search ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([2, 1])
outlet_id = c1.selectbox("Select Outlet ID", df['Outlet_ID'].tolist())
row = df[df['Outlet_ID'] == outlet_id].iloc[0]

st.markdown("---")

# ── Header KPIs ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Outlet Type",   row['Outlet_Type'])
c2.metric("Size",          row['Outlet_Size'])
c3.metric("Province",      row['Province'])
c4.metric("Distributor",   row['Distributor_ID'])
c5.metric("Coolers",       int(row['Cooler_Count']))
c6.metric("Constrained?",  "Yes ⚠️" if row['is_constrained'] else "No ✅")

st.markdown("---")

# ── Volume comparison ─────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("📦 Volume: Historical vs Predicted")
    fig = go.Figure()
    fig.add_bar(
        x=['Historical Avg', 'Observed Max', 'Predicted Jan 2026'],
        y=[row['observed_avg_monthly'], row['observed_max_monthly'],
           row['predicted_jan_2026_potential']],
        marker_color=['#636EFA', '#EF553B', '#00CC96'],
        text=[f"{row['observed_avg_monthly']:.0f}L",
              f"{row['observed_max_monthly']:.0f}L",
              f"{row['predicted_jan_2026_potential']:.0f}L"],
        textposition='outside'
    )
    fig.update_layout(yaxis_title="Volume (L)", showlegend=False, height=340)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📐 Key Metrics")
    m1, m2 = st.columns(2)
    m1.metric("Historical Avg (L)",       f"{row['observed_avg_monthly']:.1f}")
    m2.metric("Observed Max (L)",          f"{row['observed_max_monthly']:.1f}")
    m1.metric("Predicted Jan 2026 (L)",    f"{row['predicted_jan_2026_potential']:.1f}")
    m2.metric("Uplift",                    f"+{row['lift']:.0f}L ({row['lift_pct']:.1f}%)")
    m1.metric("Jan Seasonality Score",     f"{row['jan_seasonality_score']:.2f}")
    m2.metric("Growth Ratio",              f"{row['growth_ratio']:.3f}")
    m1.metric("Censorship Ratio",          f"{row['censorship_ratio']:.3f}")
    m2.metric("POI Density",               f"{row['poi_relative_density']:.3f}")

st.markdown("---")

# ── SHAP ──────────────────────────────────────────────────────────────────────
st.subheader("🧠 Top Factors Driving This Score")

features = [row['shap_feature_1'], row['shap_feature_2'], row['shap_feature_3']]
values   = [row['shap_value_1'],   row['shap_value_2'],   row['shap_value_3']]
colors   = ['#00CC96' if v > 0 else '#EF553B' for v in values]

fig = go.Figure(go.Bar(
    x=values,
    y=[f.replace('_',' ').title() for f in features],
    orientation='h',
    marker_color=colors,
    text=[f"{v:+.3f}" for v in values],
    textposition='outside'
))
fig.update_layout(
    xaxis_title="SHAP Impact on Prediction",
    height=200,
    margin=dict(l=10, r=40, t=10, b=10)
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── AI Explanation ────────────────────────────────────────────────────────────
st.subheader("💬 AI Explanation")

# Show stored explanation
st.info(row['ai_explanation'])

# Live generation button
API_KEY = os.environ.get("OPENROUTER_API_KEY", None)
if API_KEY:
    if st.button("🔄 Generate Live AI Explanation", type="primary"):
        with st.spinner("Generating via Gemma 3 (OpenRouter)..."):
            try:
                prompt = f"""You are a beverage trade marketing analyst in Sri Lanka.
Explain this outlet's sales potential to a non-technical Sales Manager in 3-4 sentences.

OUTLET: {outlet_id} | {row['Outlet_Type']} ({row['Outlet_Size']}) | {row['Distributor_ID']} | {row['Province']}
Coolers: {int(row['Cooler_Count'])} | Supply-constrained: {bool(row['is_constrained'])}
Historical avg: {row['observed_avg_monthly']:.0f}L/month | Observed max: {row['observed_max_monthly']:.0f}L/month
Predicted Jan 2026: {row['predicted_jan_2026_potential']:.0f}L/month ({row['lift_pct']:.1f}% uplift)
Jan seasonality: {row['jan_seasonality_score']:.2f} | Growth trend: {row['growth_ratio']:.3f}
Competitor density: {row.get('competitor_density', 0):.3f} | POI density: {row['poi_relative_density']:.3f}

Top factors: {features[0]}({values[0]:+.2f}), {features[1]}({values[1]:+.2f}), {features[2]}({values[2]:+.2f})
{'Budget allocated: LKR ' + f"{row['Trade_Spend_Allocation_LKR']:,.0f}" if row.get('Trade_Spend_Allocation_LKR', 0) > 0 else ''}

Write 3-4 sentences: why this score, what the key opportunity is, and what the sales team should do.
Plain English, no jargon, be specific and actionable."""

                resp = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                    json={"model": "meta-llama/llama-3.1-8b-instruct:free",
                          "max_tokens": 300,
                          "messages": [{"role": "user", "content": prompt}]},
                    timeout=30
                )
                if resp.status_code == 200:
                    live = resp.json()['choices'][0]['message']['content']
                    st.success("✅ Live explanation generated")
                    st.info(live)
                else:
                    st.error(f"API error {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.caption("_Set `OPENROUTER_API_KEY` environment variable to enable live generation._")

# ── Budget (Western only) ─────────────────────────────────────────────────────
if row['Province'] == 'Western':
    st.markdown("---")
    st.subheader("💰 Trade Budget Allocation")
    spend = row.get('Trade_Spend_Allocation_LKR', 0)
    if spend > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("Spend Allocated",    f"LKR {spend:,.0f}")
        c2.metric("Est. Volume Uplift", f"{spend/1000*0.01*row['predicted_jan_2026_potential']:.0f} L")
        c3.metric("ROI",                f"{row['predicted_jan_2026_potential']/max(spend/1000,1):.1f} L per LKR 1K")
    else:
        st.info("This outlet was not selected for trade spend in the current allocation cycle.")

# ── Sales history ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📈 Sales History")
try:
    tx = load_transactions()
    outlet_tx = tx[tx['Outlet_ID'] == outlet_id]
    if len(outlet_tx) > 0:
        monthly = (
            outlet_tx.groupby(['Year','Month'])['Volume_Liters']
            .sum().reset_index()
        )
        monthly['Period'] = (monthly['Year'].astype(str) + '-' +
                             monthly['Month'].astype(str).str.zfill(2))
        monthly = monthly.sort_values('Period')

        fig = go.Figure()
        fig.add_scatter(
            x=monthly['Period'], y=monthly['Volume_Liters'],
            mode='lines+markers', name='Actual Volume',
            line=dict(color='#636EFA', width=2)
        )
        fig.add_hline(y=row['predicted_jan_2026_potential'],
                      line_dash='dash', line_color='#00CC96',
                      annotation_text=f"Predicted: {row['predicted_jan_2026_potential']:.0f}L")
        fig.add_hline(y=row['observed_avg_monthly'],
                      line_dash='dot', line_color='#EF553B',
                      annotation_text=f"Avg: {row['observed_avg_monthly']:.0f}L")
        fig.update_layout(yaxis_title="Volume (L)", xaxis_tickangle=-45, height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transaction history found for this outlet.")
except Exception:
    st.info("Transaction history not available.")

# ── Location ──────────────────────────────────────────────────────────────────
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
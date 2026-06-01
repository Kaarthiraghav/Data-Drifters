import pandas as pd
import numpy as np
import streamlit as st

PROVINCE_MAP = {
    'DIST_W_01': 'Western',  'DIST_W_02': 'Western',  'DIST_W_03': 'Western',
    'DIST_C_01': 'Central',  'DIST_C_02': 'Central',  'DIST_C_03': 'Central',
    'DIST_NW_01': 'North-Western', 'DIST_NW_02': 'North-Western',
    'DIST_S_01': 'Southern', 'DIST_S_02': 'Southern',
}

@st.cache_data
def load_data():
    # Core predictions
    preds = pd.read_csv('../output/Data_Drifters_predictions.csv')
    # Gold features
    feat  = pd.read_csv('../gold/outlet_features.csv')
    # Coordinates
    coords = pd.read_csv('../silver/outlet_coordinates.csv')

    df = preds.merge(
        feat[[
            'Outlet_ID','Distributor_ID','Outlet_Type','Outlet_Size',
            'Cooler_Count','censorship_ratio','coeff_of_variation',
            'poi_total_count','nearby_outlet_count','poi_relative_density',
            'jan_holiday_count','avg_bill_value',
            'competitor_density' if 'competitor_density' in feat.columns else 'nearby_outlet_count',
        ]].rename(columns={'nearby_outlet_count':'competitor_density'}
                  if 'competitor_density' not in feat.columns else {}),
        on='Outlet_ID', how='left'
    )
    df = df.merge(coords, on='Outlet_ID', how='left')
    df['Province'] = df['Distributor_ID'].map(PROVINCE_MAP).fillna('Unknown')
    df['lift']     = (df['predicted_jan_2026_potential'] - df['observed_avg_monthly']).round(1)
    df['lift_pct'] = (df['lift'] / df['observed_avg_monthly'].replace(0, np.nan) * 100).round(1)

    # Budget
    try:
        budget = pd.read_csv('../output/Data_Drifters_budget_allocations.csv')
        df = df.merge(budget, on='Outlet_ID', how='left')
        col = 'Trade_Spend_Allocation_LKR'
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].fillna(0)
    except FileNotFoundError:
        df['Trade_Spend_Allocation_LKR'] = 0.0

    # AI explanations
    try:
        expl = pd.read_csv('../output/outlet_ai_explanations.csv')
        df = df.merge(expl[['Outlet_ID','ai_explanation']], on='Outlet_ID', how='left')
    except FileNotFoundError:
        df['ai_explanation'] = None

    # Fallback for missing explanations
    def _fallback(r):
        opp = "supply-constrained" if r['is_constrained'] else "showing organic growth"
        lvl = "high" if r['lift_pct'] > 60 else "moderate" if r['lift_pct'] > 25 else "low"
        return (
            f"This {r['Outlet_Type']} in {r['Province']} Province is {opp}, "
            f"with a {lvl} uplift potential of {r['lift_pct']:.1f}% above its "
            f"historical average of {r['observed_avg_monthly']:.0f}L/month. "
            f"{'Prioritise cooler deployment and discount incentives.' if r['lift_pct'] > 50 else 'Support with light merchandising.'}"
        )
    mask = df['ai_explanation'].isna() | df['ai_explanation'].isin(['Data unavailable','Unavailable',''])
    df.loc[mask, 'ai_explanation'] = df[mask].apply(_fallback, axis=1)

    # SHAP placeholder columns (real ones come from notebook)
    if 'shap_feature_1' not in df.columns:
        df['shap_feature_1'] = 'censorship_ratio'
        df['shap_value_1']   = df['censorship_ratio'].fillna(0).round(3)
        df['shap_feature_2'] = 'poi_relative_density'
        df['shap_value_2']   = df['poi_relative_density'].fillna(0).round(3)
        df['shap_feature_3'] = 'growth_ratio'
        df['shap_value_3']   = df['growth_ratio'].fillna(0).round(3)

    return df

@st.cache_data
def load_transactions():
    return pd.read_csv('../silver/transactions_clean.csv')
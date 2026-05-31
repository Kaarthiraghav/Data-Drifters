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
    predictions = pd.read_csv('../output/Data_Drifters_predictions.csv')
    features    = pd.read_csv('../gold/outlet_features.csv')
    coords      = pd.read_csv('../silver/outlet_coordinates.csv')

    # Merge
    df = predictions.merge(
        features[[
            'Outlet_ID', 'Distributor_ID', 'Outlet_Type', 'Outlet_Size',
            'Cooler_Count', 'censorship_ratio', 'coeff_of_variation',
            'poi_total_count', 'nearby_outlet_count', 'poi_relative_density',
            'jan_holiday_count', 'avg_bill_value', 'competitor_density',
        ]],
        on='Outlet_ID', how='left'
    )
    df = df.merge(coords, on='Outlet_ID', how='left')

    # Province
    df['Province'] = df['Distributor_ID'].map(PROVINCE_MAP).fillna('Unknown')

    # Derived
    df['lift']     = (df['predicted_jan_2026_potential'] - df['observed_avg_monthly']).round(1)
    df['lift_pct'] = (df['lift'] / df['observed_avg_monthly'].replace(0, np.nan) * 100).round(1)

    # Budget allocation — load if exists, else zeros
    try:
        budget = pd.read_csv('../output/Data_Drifters_budget_allocations.csv')
        df = df.merge(budget, on='Outlet_ID', how='left')
        df['Trade_Spend_Allocation_LKR'] = df['Trade_Spend_Allocation_LKR'].fillna(0)
    except FileNotFoundError:
        df['Trade_Spend_Allocation_LKR'] = 0.0

    # AI explanations — load if exists, else fallback
    try:
        explanations = pd.read_csv('../output/outlet_ai_explanations.csv')
        df = df.merge(explanations[['Outlet_ID', 'ai_explanation']], on='Outlet_ID', how='left')
    except FileNotFoundError:
        df['ai_explanation'] = None

    # Fallback explanation for missing
    mask = df['ai_explanation'].isna() | (df['ai_explanation'] == 'Explanation unavailable')
    df.loc[mask, 'ai_explanation'] = df[mask].apply(lambda r: (
        f"This {r.get('Outlet_Type','outlet')} is predicted to reach "
        f"{r['predicted_jan_2026_potential']:.0f}L in January 2026, "
        f"a {r['lift_pct']:.1f}% uplift over its historical average of "
        f"{r['observed_avg_monthly']:.0f}L. "
        f"{'Supply constraints have historically capped this outlet below its true demand.' if r['is_constrained'] else 'This outlet is operating closer to its natural ceiling.'} "
        f"Recommendation: {'Prioritise for cooler deployment and discount incentives.' if r['lift_pct'] > 50 else 'Support with light merchandising.'}"
    ), axis=1)

    # SHAP columns — load if exists, else use feature values as proxy
    shap_cols = ['shap_feature_1','shap_value_1','shap_feature_2','shap_value_2','shap_feature_3','shap_value_3']
    if not all(c in df.columns for c in shap_cols):
        df['shap_feature_1'] = 'censorship_ratio'
        df['shap_value_1']   = df['censorship_ratio'].fillna(0).round(3)
        df['shap_feature_2'] = 'competitor_density'
        df['shap_value_2']   = df['competitor_density'].fillna(0).round(3)
        df['shap_feature_3'] = 'growth_ratio'
        df['shap_value_3']   = df['growth_ratio'].fillna(0).round(3)

    return df


@st.cache_data
def load_transactions():
    return pd.read_csv('../silver/transactions_clean.csv')
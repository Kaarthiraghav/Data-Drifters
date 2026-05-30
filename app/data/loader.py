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
    # Load each file
    features    = pd.read_csv('../gold/outlet_features.csv')
    predictions = pd.read_csv('../output/Data_Drifters_predictions.csv')
    master      = pd.read_csv('../silver/outlet_master.csv')
    coords      = pd.read_csv('../silver/outlet_coordinates.csv')

    # Merge everything on Outlet_ID
    df = predictions.merge(features[[ 
        'Outlet_ID', 'Distributor_ID', 'Outlet_Type', 'Outlet_Size',
        'Cooler_Count', 'censorship_ratio', 'coeff_of_variation',
        'poi_total_count', 'nearby_outlet_count', 'poi_relative_density',
        'jan_holiday_count', 'avg_bill_value'
    ]], on='Outlet_ID', how='left')

    df = df.merge(coords, on='Outlet_ID', how='left')

    # Add province
    df['Province'] = df['Distributor_ID'].map(PROVINCE_MAP).fillna('Unknown')

    # Derived columns
    df['lift']     = df['predicted_jan_2026_potential'] - df['observed_avg_monthly']
    df['lift_pct'] = (df['lift'] / df['observed_avg_monthly'] * 100).round(1)

    # Placeholder columns for SHAP + LLM (swap when teammates deliver)
    if 'shap_feature_1' not in df.columns:
        df['shap_feature_1'] = 'censorship_ratio'
        df['shap_value_1']   = df['censorship_ratio'].round(3)
        df['shap_feature_2'] = 'poi_relative_density'
        df['shap_value_2']   = df['poi_relative_density'].round(3)
        df['shap_feature_3'] = 'growth_ratio'
        df['shap_value_3']   = df['growth_ratio'].round(3)

    if 'llm_explanation' not in df.columns:
        df['llm_explanation'] = df.apply(lambda r: (
            f"This {r['Outlet_Type']} is predicted to reach "
            f"{r['predicted_jan_2026_potential']:.0f}L in January 2026, "
            f"a {r['lift_pct']:.1f}% uplift over its historical average of "
            f"{r['observed_avg_monthly']:.0f}L. "
            f"Key driver: censorship ratio of {r['censorship_ratio']:.2f} "
            f"suggests supply constraints have capped past sales."
        ), axis=1)

    if 'trade_spend_lkr' not in df.columns:
        df['trade_spend_lkr'] = 0.0
        df['spend_type']      = 'none'

    return df


def load_transactions():
    return pd.read_csv('../silver/transactions_clean.csv')
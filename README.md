# Data Storm 7.0 — Data-Drifters Pipeline

A comprehensive three-layer (Bronze → Silver → Gold) ETL and ML pipeline for demand forecasting and POI enrichment. This project ingests raw sales and outlet data, applies rigorous data quality checks, engineers features, and predicts January 2026 demand potential for outlets across Sri Lanka.

## Features

- **Bronze Layer**: Raw CSV ingestion with metadata tracking
- **Silver Layer**: Deterministic data quality checks and rejection handling
- **Gold Layer**: Feature engineering, POI enrichment, and clustering
- **Modeling**: Ensemble XGBoost + peer-group ceiling + seasonal adjustments
- **Outputs**: Cleaned tables, EDA plots, and final predictions

## Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM (8GB+ recommended for full POI downloads)
- **Disk**: ~500MB for raw data + processed tables

### Python Libraries

Install all dependencies via pip:

```bash
pip install -r requirements.txt
```

Or manually install the packages listed below:

#### Core Data Processing
- `pandas >= 1.3.0` — DataFrames and tabular operations
- `numpy >= 1.20.0` — Numerical computations
- `pyarrow >= 5.0.0` — Parquet support (optional, for faster I/O)

#### Machine Learning & Modeling
- `scikit-learn >= 0.24.0` — OrdinalEncoder, KFold, metrics
- `xgboost >= 1.5.0` — Gradient boosting models (quantile + mean objectives)

#### Visualization
- `matplotlib >= 3.3.0` — Plotting (line, scatter, histogram, heatmap)
- `seaborn >= 0.11.0` — Statistical visualization

#### Geospatial
- `requests >= 2.25.0` — HTTP requests for Overpass API
- `scikit-learn` (also provides `BallTree` for spatial indexing)

#### Notebooks & Execution
- `jupyter >= 1.0.0` — Jupyter Lab/Notebook environment (optional, for interactive use)
- `nbconvert >= 6.0.0` — Convert/execute notebooks from command line (optional)

### Optional for Development
- `ipython >= 7.0.0` — Enhanced REPL

## Installation

### 1. Clone or download the project

```bash
cd /path/to/Data-Drifters
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Or install directly:

```bash
pip install pandas numpy scikit-learn xgboost matplotlib seaborn requests jupyter nbconvert
```

## Quick Start

### Run the full pipeline from the notebook

**Interactive (Jupyter)**:
```bash
jupyter notebook code_improved.ipynb
# Then execute all cells in order
```

**Batch execution**:
```bash
python -m nbconvert --to notebook --execute code_improved.ipynb \
  --ExecutePreprocessor.timeout=600 \
  --output code_improved_executed.ipynb
```

### Expected runtime
- **Bronze + Silver**: ~2–5 minutes
- **Gold + Features**: ~1–2 minutes
- **POI downloads** (Overpass API): ~3–5 minutes (cached after first run)
- **Modeling + EDA**: ~2–3 minutes
- **Total**: ~10–15 minutes

## Project Structure

```
Data-Drifters/
├── code.ipynb          # Main pipeline notebook
├── README.md                    # This file
│
├── data/                        # Raw input CSVs
│   ├── transactions_history_final.csv
│   ├── outlet_master.csv
│   ├── outlet_coordinates.csv
│   ├── distributor_seasonality_details.csv
│   └── holiday_list.csv
│
├── bronze/                      # Raw ingestion (pickles + CSVs + samples)
│   ├── transactions.pkl
│   ├── outlet_master.pkl
│   ├── outlet_coordinates.pkl
│   ├── distributor_seasonality.pkl
│   ├── holiday_list.pkl
│   ├── *_sample_1k.csv          # 1K-row samples for quick inspection
│   └── ingestion_metadata.json  # Metadata per dataset
│
├── silver/                      # Cleaned tables after DQ checks
│   ├── transactions_clean.csv
│   ├── outlet_master.csv
│   ├── outlet_coordinates.csv
│   ├── distributor_seasonality.csv
│   ├── holiday_list.csv
│   └── rejected/                # Rows failing DQ checks
│       ├── transactions_rejected.csv
│       ├── outlet_master_rejected.csv
│       ├── outlet_coordinates_rejected.csv
│       ├── distributor_seasonality_rejected.csv
│       └── holiday_list_rejected.csv
│
├── gold/                        # Features and analysis outputs
│   ├── outlet_features.csv      # Final feature table (one row per outlet)
│   ├── outlet_features.pkl      # Pickled version (faster load)
│   ├── poi_raw.pkl              # Cached POI data from Overpass
│   ├── eda_01_data_forensics.png
│   ├── eda_02_volume_by_type_size.png
│   ├── eda_03_censorship_analysis.png
│   ├── eda_04_correlation_heatmap.png
│   ├── eda_05_geographic_maps.png
│   ├── eda_06_poi_validation.png
│   └── eda_07_censorship_deep_dive.png
│
└── output/                      # Final predictions
    ├── Data_Drifters_predictions.csv  # Per-outlet Jan 2026 demand estimates
    └── validation_distribution.png
```

## Pipeline Stages

### Stage 1: Bronze (Raw Ingestion)
- Load each raw CSV as-is
- Save as pickle (fast reload) and CSV
- Generate 1K-row sample for validation
- Record metadata (rows, columns, nulls, memory usage)

### Stage 2: Silver (Data Quality & Cleaning)
Data quality checks applied:
- **Null checks**: Flag rows with missing critical fields
- **Format validation**: Regex patterns (IDs, dates)
- **Referential integrity**: Cross-table key validation
- **Value ranges**: Numeric bounds (year, month, coordinates)
- **Outlier detection**: IQR method per group
- **Duplicate resolution**: Keep best row by sort column
- **Domain corrections**: Fix typos, normalize casing

Rejected rows saved with rejection reason and timestamp.

### Stage 3: Gold (Feature Engineering)

#### Transaction-level features
- `avg_monthly_volume`, `max_monthly_volume`, `std_monthly_volume`
- `total_volume`, `active_months`, `unique_skus`, `avg_sku_breadth`
- `transaction_count`

#### Constraint indicators
- `censorship_ratio` = max / mean (detect supply ceilings)
- `coeff_of_variation` = std / mean (detect unnatural stability)
- `is_constrained` = binary flag (10th percentile threshold)

#### Trend features
- `growth_ratio` = recent avg / older avg (recent vs historical)

#### Outlet attributes (from master table)
- `Outlet_Type`, `Outlet_Size`, `Cooler_Count`, `size_score`

#### Geographic & POI enrichment
- `Latitude`, `Longitude`, `has_coords` flag
- `radius_m` (500m for Western/urban, 1000m otherwise)
- Per-category POI counts: `poi_schools_count`, `poi_hospitals_count`, etc.
- Nearest distances: `nearest_schools_m`, `nearest_hospitals_m`, etc.
- `poi_total_count`, `poi_relative_density`, `nearby_outlet_count`

#### Adjustment factors
- `jan_seasonality_score` (1.0 or 1.2 per distributor)
- `is_favorable_jan` (binary)
- `jan_holiday_count` (number of public holidays in January)

### Stage 4: Modeling

**Training set**: Unconstrained outlets (observed demand is uncensored)

**Models**:
1. **XGBoost Mean** — central tendency estimate
2. **XGBoost Quantile (90th pctile)** — upper-bound estimate
3. **Peer-group Ceiling** — group-level max by `(Outlet_Type, Outlet_Size)`

**Ensemble**:
- Weighted combination: `0.40 × mean + 0.35 × q90 + 0.25 × peer_ceiling`
- Weights tuned by 5-fold CV on unconstrained set

**Adjustments (for January 2026)**:
- Apply `jan_seasonality_score` (seasonal index)
- Apply `growth_ratio` (capped at 1.5 for stability)
- Apply holiday factor (20 working days / 22 = 0.909)
- Enforce guardrails:
  - **Constrained floor**: observed max (must exceed censored baseline)
  - **Unconstrained floor**: avg monthly × 0.5
  - **Ceiling**: max monthly × 5.0

### Stage 5: Outputs

**output/Data_Drifters_predictions.csv** (columns):
- `Outlet_ID`
- `predicted_jan_2026_potential` — final demand estimate for January 2026
- `base_potential` — ensemble output before seasonal adjustments
- `ensemble_raw` — raw ensemble before guardrails
- `observed_avg_monthly` — historical average
- `observed_max_monthly` — historical peak
- `is_constrained` — flag (1 = supply-constrained)
- `jan_seasonality_score` — seasonal multiplier applied
- `growth_ratio` — recent vs historical trend

## Key Parameters & Thresholds

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Constrained threshold (censorship ratio) | 10th percentile | Data-driven; adaptive to distribution |
| XGBoost learning rate | 0.05 | Conservative, stable convergence |
| XGBoost max depth | 5 | Prevent overfitting; match unconstrained set size |
| Quantile level | 0.90 | Optimistic but realistic estimate |
| POI radius — Western province | 500m | Dense urban environment |
| POI radius — Other provinces | 1000m | Sparse rural environment |
| January growth cap | 1.5× | Prevent wild extrapolation |
| Holiday factor | 20/22 | 2 public holidays, 22 working days |
| Peer ceiling percentile | 75th pctile | Robust central-upper estimate |

## Configuration & Customization

Edit the constants in the notebook to adjust:

```python
# Paths
DATA_PATHS = {
    'raw': 'data/',
    'bronze': 'bronze/',
    'silver': 'silver/',
    'gold': 'gold/',
    'output': 'output/',
}

# Validation ranges (Sri Lanka-specific)
SL_LAT_RANGE = (5.9, 9.9)
SL_LON_RANGE = (79.4, 82.0)
YEAR_RANGE = (2023, 2025)
MONTH_RANGE = (1, 12)

# Model parameters
XGB_PARAMS_MEAN = {
    'learning_rate': 0.05,
    'max_depth': 5,
    'n_estimators': 500,
    ...
}
```

## Troubleshooting

### Issue: "Module not found: xgboost"
**Solution**: Install it explicitly:
```bash
pip install xgboost==1.7.0
```

### Issue: Overpass API timeout
**Solution**: The POI download uses a cache (`gold/poi_raw.pkl`). If first run times out, re-run the cell; subsequent runs load from cache.

### Issue: Out of memory
**Solution**: Reduce sample sizes or run on a machine with 8GB+ RAM. POI downloads are the memory-intensive step.

### Issue: Slow performance on macOS
**Solution**: Ensure `scikit-learn` uses OpenBLAS:
```bash
pip install scikit-learn[mkl]  # or use conda for conda-forge packages
```

## Performance Metrics

From the notebook output (example):
- **Training set**: ~19,204 unconstrained outlets
- **Prediction set**: ~1,766 constrained outlets
- **Features**: 40+ derived features
- **CV R² (XGBoost mean)**: 0.75 ± 0.02
- **Constrained above baseline**: 98.5%
- **Median uplift (constrained)**: 1.18× observed max

## Citation & Attribution

Data provided by internal sources. Notebook implements a deterministic, auditable pipeline using open-source tools (pandas, scikit-learn, XGBoost, Overpass).

## Support & Further Reading

- **XGBoost quantile regression**: https://xgboost.readthedocs.io/
- **Scikit-learn preprocessing**: https://scikit-learn.org/stable/modules/preprocessing.html
- **Overpass API**: https://wiki.openstreetmap.org/wiki/Overpass_API
- **Technical report**: See `Report.latex`

---

**Last updated**: May 2026  
**Project**: Data Storm 7.0 — Data-Drifters

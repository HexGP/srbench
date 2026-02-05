"""Convert Agriculture CSVs to SRBench TSV.GZ with TRANSFORMED targets (log version).

This is a copy of csv_to_tsvgz_agric.py with one change: the target column is
transformed (same as codes/Agriculture/mtr_ginn_agric_sym.py) before writing.
Metrics from SRBench on these datasets are then in the same space as GINN-LP
and MTRGINN-LP for fair comparison.

- Original pipeline: csv_to_tsvgz_agric.py (raw targets).
- This pipeline: csv_to_tsvgz_agric_log.py (transformed targets).
"""
import csv
import gzip
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

SRB = os.path.dirname(os.path.abspath(__file__))
DATA_AGRIC = os.path.join(SRB, "data_agric")

# Configuration (same as csv_to_tsvgz_agric.py)
SAMPLE_FRACTION = 0.1
RANDOM_STATE_SAMPLE = 42
RANDOM_STATE_SPLIT = 100

TARGETS = {
    "sustainability": "Sustainability_Score",
    "consumer_trend": "Consumer_Trend_Index"
}

def get_dataset_name(base_name, sample_fraction, log_suffix=True):
    """Generate dataset name with sample fraction and _log suffix."""
    if sample_fraction == 0.1:
        name = f"agric_01_{base_name}"
    elif sample_fraction == 0.01:
        name = f"agric_001_{base_name}"
    else:
        frac_str = str(int(sample_fraction * 1000)).zfill(3)
        name = f"agric_{frac_str}_{base_name}"
    if log_suffix:
        name = name + "_log"
    return name

def process_agriculture_data(sample_fraction=0.1):
    """Process agriculture data (same as csv_to_tsvgz_agric.py)."""
    fa_ds = pd.read_csv(os.path.join(DATA_AGRIC, 'farmer_advisor_dataset.csv'))
    mr_ds = pd.read_csv(os.path.join(DATA_AGRIC, 'market_researcher_dataset.csv'))

    print(f"Loaded farmer_advisor: {len(fa_ds)} rows")
    print(f"Loaded market_researcher: {len(mr_ds)} rows")

    if sample_fraction is not None and 0 < sample_fraction < 1:
        fa_ds = fa_ds.sample(frac=sample_fraction, random_state=RANDOM_STATE_SAMPLE)
        mr_ds = mr_ds.sample(frac=sample_fraction, random_state=RANDOM_STATE_SAMPLE)
        print(f"After sampling ({sample_fraction}): {len(fa_ds)} rows each")

    fa_ds.sort_values('Crop_Type', inplace=True)
    mr_ds.sort_values('Product', inplace=True)

    df_mrg = pd.merge(fa_ds, mr_ds, left_on='Crop_Type', right_on='Product', how='inner').drop(
        ['Farm_ID', 'Market_ID', 'Product'], axis=1
    )
    print(f"After merge: {len(df_mrg)} rows")

    df_mrg = df_mrg[[
        'Crop_Type', 'Soil_pH', 'Soil_Moisture', 'Temperature_C', 'Rainfall_mm',
        'Fertilizer_Usage_kg', 'Pesticide_Usage_kg', 'Crop_Yield_ton',
        'Market_Price_per_ton', 'Demand_Index', 'Supply_Index', 'Competitor_Price_per_ton', 'Economic_Indicator',
        'Weather_Impact_Score', 'Seasonal_Factor', 'Sustainability_Score', 'Consumer_Trend_Index'
    ]]

    df_mrg.dropna(inplace=True)
    print(f"After dropna: {len(df_mrg)} rows")

    for col in df_mrg.select_dtypes(include=['object']).columns:
        df_mrg[col] = df_mrg[col].astype('category')

    df = df_mrg.copy()
    for c in ['Crop_Type', 'Seasonal_Factor']:
        if c in df.columns:
            le = LabelEncoder()
            df[c] = le.fit_transform(df[c])
            print(f"Encoded {c}: {len(le.classes_)} unique values")

    return df

def create_dataset(df, dataset_name, target_col, sample_fraction=0.1):
    """
    Create a single-target dataset for SRBench with TRANSFORMED targets.
    Target values are transformed (same as codes/Agriculture) before writing.
    """
    feature_cols = [col for col in df.columns if col not in ['Sustainability_Score', 'Consumer_Trend_Index']]
    raw_target = np.asarray(df[target_col], dtype=float)
    if np.any(raw_target <= 0):
        raise ValueError(f"Target {target_col} has non-positive values; transform requires positive targets.")
    target_data = np.log(raw_target)

    out_dir = os.path.join(SRB, dataset_name)
    os.makedirs(out_dir, exist_ok=True)

    tsv_gz_path = os.path.join(out_dir, f"{dataset_name}.tsv.gz")

    data_rows = []
    for idx, row in df.iterrows():
        feature_values = [str(row[col]) for col in feature_cols]
        target_value = str(target_data[idx])
        data_rows.append(feature_values + [target_value])

    with gzip.open(tsv_gz_path, "wt", encoding="utf-8") as f_out:
        w = csv.writer(f_out, delimiter="\t")
        w.writerow(feature_cols + ["target"])
        w.writerows(data_rows)

    print(f"Created {tsv_gz_path}: {len(data_rows)} rows, {len(feature_cols)} features (targets transformed)")

    metadata_path = os.path.join(out_dir, "metadata.yaml")
    with open(metadata_path, "w") as f:
        f.write(f"dataset: {dataset_name}\n")
        f.write(f"description: Agriculture dataset - {target_col}. {len(feature_cols)} features, single target. Sample fraction: {sample_fraction}. Targets in transformed space for fair comparison with GINN-LP/MTRGINN-LP.\n")
        f.write("task: regression\n")
        f.write("target:\n")
        f.write("  type: continuous\n")
        f.write(f"  description: {target_col} (transformed)\n")
        f.write("features:\n")
        for col in feature_cols:
            f.write(f"  - name: {col}\n")
            f.write("    type: continuous\n")

    print(f"Created {metadata_path}")

    return tsv_gz_path, len(data_rows), len(feature_cols)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            sample_frac = float(sys.argv[1])
            if not (0 < sample_frac <= 1):
                raise ValueError("Sample fraction must be between 0 and 1")
        except ValueError as e:
            print(f"Error: Invalid sample fraction '{sys.argv[1]}'. {e}")
            print("Usage: python csv_to_tsvgz_agric_log.py [sample_fraction]")
            print("Example: python csv_to_tsvgz_agric_log.py 0.1")
            print("Example: python csv_to_tsvgz_agric_log.py 0.01")
            sys.exit(1)
    else:
        sample_frac = SAMPLE_FRACTION

    print("=" * 60)
    print("Agriculture CSVs -> SRBench TSV.GZ (LOG / transformed targets)")
    print("=" * 60)
    print(f"Sample fraction: {sample_frac}")
    print("Targets will be transformed (same as codes/Agriculture) for fair comparison with GINN-LP.")
    print()

    df = process_agriculture_data(sample_fraction=sample_frac)
    print()

    results = []
    for base_name, target_col in TARGETS.items():
        dataset_name = get_dataset_name(base_name, sample_frac, log_suffix=True)
        print(f"\nCreating dataset: {dataset_name} (target: {target_col}, transformed)")
        print("-" * 60)
        tsv_path, n_rows, n_features = create_dataset(df, dataset_name, target_col, sample_frac)
        results.append((dataset_name, n_rows, n_features))

    print("\n" + "=" * 60)
    print("Conversion complete (log version).")
    print("=" * 60)
    for name, rows, features in results:
        print(f"  {name}: {rows} rows, {features} features")

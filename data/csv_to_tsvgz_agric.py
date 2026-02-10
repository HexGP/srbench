"""Convert Agriculture CSVs to TSV.GZ in SRBench layout.
Uses codes/Agriculture/mtr_ginn_agric_sym.py as template (Option 2: merge, then single target).

Data is prepared the same way as mtr_ginn_agric_sym.py (same CSVs, sampling, merge, columns,
dropna, categorical encoding, LabelEncoder on Crop_Type and Seasonal_Factor) but:
- No MinMaxScaler on features (data is not scaled).
- No log-transform on targets (targets are raw Sustainability_Score / Consumer_Trend_Index).
- No train/test split here (SRBench does the split when loading).

So the TSV.GZ files in agric_01_*, agric_001_* contain raw, unscaled feature and target values.
"""
import csv
import gzip
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

SRB = os.path.dirname(os.path.abspath(__file__))
DATA_AGRIC = os.path.join(SRB, "data_agric")

# Configuration
SAMPLE_FRACTION = 0.1  # Can be changed to 0.01 for smaller dataset
RANDOM_STATE_SAMPLE = 42  # For sampling (matching codes/Agriculture/mtr_ginn_agric_sym.py line 30-31)
RANDOM_STATE_SPLIT = 100  # For train/test split (not used here, but for reference - matches codes/Agriculture/mtr_ginn_agric_sym.py line 306)

# Target columns (will create separate datasets for each)
# Note: Sample fraction will be prefixed to dataset names (e.g., agric_01_sustainability for 0.1)
TARGETS = {
    "sustainability": "Sustainability_Score",
    "consumer_trend": "Consumer_Trend_Index"
}

def get_dataset_name(base_name, sample_fraction):
    """Generate dataset name with sample fraction prefix."""
    if sample_fraction == 0.1:
        return f"agric_01_{base_name}"
    elif sample_fraction == 0.01:
        return f"agric_001_{base_name}"
    else:
        # For other fractions, use the fraction as string (e.g., 0.05 -> "005")
        frac_str = str(int(sample_fraction * 1000)).zfill(3)
        return f"agric_{frac_str}_{base_name}"

def process_agriculture_data(sample_fraction=0.1):
    """
    Process agriculture data following the same steps as mtr_ginn_agric_sym.py
    Returns: processed DataFrame with all features and both targets
    """
    # Load raw CSVs
    fa_ds = pd.read_csv(os.path.join(DATA_AGRIC, 'farmer_advisor_dataset.csv'))
    mr_ds = pd.read_csv(os.path.join(DATA_AGRIC, 'market_researcher_dataset.csv'))
    
    print(f"Loaded farmer_advisor: {len(fa_ds)} rows")
    print(f"Loaded market_researcher: {len(mr_ds)} rows")
    
    # Optional sampling
    if sample_fraction is not None and 0 < sample_fraction < 1:
        fa_ds = fa_ds.sample(frac=sample_fraction, random_state=RANDOM_STATE_SAMPLE)
        mr_ds = mr_ds.sample(frac=sample_fraction, random_state=RANDOM_STATE_SAMPLE)
        print(f"After sampling ({sample_fraction}): {len(fa_ds)} rows each")
    
    # Sort
    fa_ds.sort_values('Crop_Type', inplace=True)
    mr_ds.sort_values('Product', inplace=True)
    
    # Merge and select columns
    df_mrg = pd.merge(fa_ds, mr_ds, left_on='Crop_Type', right_on='Product', how='inner').drop(
        ['Farm_ID', 'Market_ID', 'Product'], axis=1
    )
    print(f"After merge: {len(df_mrg)} rows")
    
    # Select specific columns (same as mtr_ginn_agric_sym.py)
    df_mrg = df_mrg[[
        'Crop_Type', 'Soil_pH', 'Soil_Moisture', 'Temperature_C', 'Rainfall_mm',
        'Fertilizer_Usage_kg', 'Pesticide_Usage_kg', 'Crop_Yield_ton',
        'Market_Price_per_ton', 'Demand_Index', 'Supply_Index', 'Competitor_Price_per_ton', 'Economic_Indicator',
        'Weather_Impact_Score', 'Seasonal_Factor', 'Sustainability_Score', 'Consumer_Trend_Index'
    ]]
    
    # Cleanup
    df_mrg.dropna(inplace=True)
    print(f"After dropna: {len(df_mrg)} rows")
    
    # Convert object columns to category
    for col in df_mrg.select_dtypes(include=['object']).columns:
        df_mrg[col] = df_mrg[col].astype('category')
    
    # Encode categoricals used in features (same as mtr_ginn_agric_sym.py)
    df = df_mrg.copy()
    for c in ['Crop_Type', 'Seasonal_Factor']:
        if c in df.columns:
            le = LabelEncoder()
            df[c] = le.fit_transform(df[c])
            print(f"Encoded {c}: {len(le.classes_)} unique values")
    
    return df

def create_dataset(df, dataset_name, target_col, sample_fraction=0.1):
    """
    Create a single-target dataset for SRBench.
    
    Args:
        df: Processed DataFrame with all features and targets
        dataset_name: Name for the dataset (e.g., 'agric_sustainability')
        target_col: Name of the target column
        sample_fraction: Sample fraction used (for naming)
    """
    # Select features (all columns except both targets)
    feature_cols = [col for col in df.columns if col not in ['Sustainability_Score', 'Consumer_Trend_Index']]
    target_data = df[target_col].values
    
    # Create output directory
    out_dir = os.path.join(SRB, dataset_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # Create TSV.GZ file
    tsv_gz_path = os.path.join(out_dir, f"{dataset_name}.tsv.gz")
    
    # Prepare data: features + target (use position i, not row index, for target_data)
    data_rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        feature_values = [str(row[col]) for col in feature_cols]
        data_rows.append(feature_values + [str(target_data[i])])
    
    # Write header + data
    with gzip.open(tsv_gz_path, "wt", encoding="utf-8") as f_out:
        w = csv.writer(f_out, delimiter="\t")
        # Write header: feature names + "target"
        w.writerow(feature_cols + ["target"])
        # Write data rows
        w.writerows(data_rows)
    
    print(f"Created {tsv_gz_path}: {len(data_rows)} rows, {len(feature_cols)} features")
    
    # Create metadata.yaml
    metadata_path = os.path.join(out_dir, "metadata.yaml")
    with open(metadata_path, "w") as f:
        f.write(f"dataset: {dataset_name}\n")
        f.write(f"description: Agriculture dataset - {target_col}. {len(feature_cols)} features, single target. Sample fraction: {sample_fraction}.\n")
        f.write("task: regression\n")
        f.write("target:\n")
        f.write("  type: continuous\n")
        f.write(f"  description: {target_col}\n")
        f.write("features:\n")
        for i, col in enumerate(feature_cols, 1):
            f.write(f"  - name: {col}\n")
            f.write("    type: continuous\n")
    
    print(f"Created {metadata_path}")
    
    return tsv_gz_path, len(data_rows), len(feature_cols)

if __name__ == "__main__":
    import sys
    
    # Allow sample fraction to be passed as command-line argument
    if len(sys.argv) > 1:
        try:
            sample_frac = float(sys.argv[1])
            if not (0 < sample_frac <= 1):
                raise ValueError("Sample fraction must be between 0 and 1")
        except ValueError as e:
            print(f"Error: Invalid sample fraction '{sys.argv[1]}'. {e}")
            print("Usage: python csv_to_tsvgz_agric.py [sample_fraction]")
            print("Example: python csv_to_tsvgz_agric.py 0.1")
            print("Example: python csv_to_tsvgz_agric.py 0.01")
            sys.exit(1)
    else:
        sample_frac = SAMPLE_FRACTION
    
    print("=" * 60)
    print("Converting Agriculture CSVs to SRBench TSV.GZ format")
    print("=" * 60)
    print(f"Sample fraction: {sample_frac}")
    print()
    
    # Process data
    df = process_agriculture_data(sample_fraction=sample_frac)
    print()
    
    # Create datasets for each target (with sample fraction in name)
    results = []
    for base_name, target_col in TARGETS.items():
        dataset_name = get_dataset_name(base_name, sample_frac)
        print(f"\nCreating dataset: {dataset_name} (target: {target_col})")
        print("-" * 60)
        tsv_path, n_rows, n_features = create_dataset(df, dataset_name, target_col, sample_frac)
        results.append((dataset_name, n_rows, n_features))
    
    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)
    for name, rows, features in results:
        print(f"  {name}: {rows} rows, {features} features")

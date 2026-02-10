"""Convert ENB data to TSV.GZ in SRBench layout.
Uses codes/ENB/mtr_ginn_sym.py as reference.

Data is prepared the same way as mtr_ginn_sym.py (same features X1..X8, targets Y1=Heating
and Y2=Cooling) but:
- No MinMaxScaler on features (data is not scaled).
- No train/test split here (SRBench does the split when loading).

Supports two input modes:
1) Single combined file: data_enb/ENB2012_data.csv with 8 feature columns + 2 target
   columns (e.g. X1..X8, Y1, Y2 or target_1, target_2). Same structure as the Excel
   used in mtr_ginn_sym.py (df.iloc[:, :-2] for X, iloc[:, -2:] for y).
2) Two separate CSVs: ENB2012_Heating_Load.csv and ENB2012_Cooling_Load.csv (each
   X1..X8 + target), used as-is with no transformation.
"""
import csv
import gzip
import os
import pandas as pd

SRB = os.path.dirname(os.path.abspath(__file__))
DATA_ENB = os.path.join(SRB, "data_enb")

# Same as mtr_ginn_sym.py: 8 features, 2 targets (Y1=Heating, Y2=Cooling)
FEATURE_COLS = [f"X{i}" for i in range(1, 9)]
TARGET_HEATING = "Y1"   # Heating Load (mtr_ginn uses iloc[:, -2])
TARGET_COOLING = "Y2"   # Cooling Load (mtr_ginn uses iloc[:, -1])

OUT_DATASETS = [
    ("enb_heating", TARGET_HEATING, "Heating Load (Y1)"),
    ("enb_cooling", TARGET_COOLING, "Cooling Load (Y2)"),
]


def load_combined_enb():
    """Load from single combined CSV (8 features + 2 targets) if present. Returns (X_df, y_heating, y_cooling) or None."""
    combined_path = os.path.join(DATA_ENB, "ENB2012_data.csv")
    if not os.path.isfile(combined_path):
        return None
    df = pd.read_csv(combined_path)
    # Expect 10 columns: 8 features + 2 targets (any names for targets)
    if len(df.columns) < 10:
        return None
    # Use last 2 columns as Y1, Y2 (same as mtr_ginn iloc[:, -2:])
    feature_cols = list(df.columns[:8])
    target_cols = list(df.columns[-2:])
    X = df[feature_cols]
    y_heating = df[target_cols[0]].values
    y_cooling = df[target_cols[1]].values
    return feature_cols, X, y_heating, y_cooling, target_cols[0], target_cols[1]


def write_tsvgz_and_metadata(out_dir, name, feature_cols, X, y, target_description):
    """Write name.tsv.gz and metadata.yaml. X is DataFrame, y is 1d array."""
    os.makedirs(out_dir, exist_ok=True)
    tsv_gz_path = os.path.join(out_dir, f"{name}.tsv.gz")
    n_rows = len(y)
    with gzip.open(tsv_gz_path, "wt", encoding="utf-8") as f_out:
        w = csv.writer(f_out, delimiter="\t")
        w.writerow(feature_cols + ["target"])
        for i in range(n_rows):
            row = [X.iloc[i, j] for j in range(len(feature_cols))] + [y[i]]
            w.writerow(row)
    print(f"Created {tsv_gz_path}: {n_rows} rows, {len(feature_cols)} features")

    metadata_path = os.path.join(out_dir, "metadata.yaml")
    with open(metadata_path, "w") as f:
        f.write(f"dataset: {name}\n")
        f.write(f"description: ENB2012 - {target_description}. 8 features (X1..X8), single target. Same prep as mtr_ginn_sym.py, no scaling, no split.\n")
        f.write("task: regression\n")
        f.write("target:\n")
        f.write("  type: continuous\n")
        f.write(f"  description: {target_description}\n")
        f.write("features:\n")
        for col in feature_cols:
            f.write(f"  - name: {col}\n")
            f.write("    type: continuous\n")
    print(f"Created {metadata_path}")


def main():
    print("=" * 60)
    print("Converting ENB data to SRBench TSV.GZ format")
    print("(Same preparation as codes/ENB/mtr_ginn_sym.py, without MinMaxScale or split)")
    print("=" * 60)

    combined = load_combined_enb()
    if combined is not None:
        feature_cols, X, y_heating, y_cooling, name_heating, name_cooling = combined
        print(f"Using combined source: ENB2012_data.csv ({len(X)} rows)")
        for (out_name, _, desc), y in [
            (OUT_DATASETS[0], y_heating),
            (OUT_DATASETS[1], y_cooling),
        ]:
            out_dir = os.path.join(SRB, out_name)
            write_tsvgz_and_metadata(out_dir, out_name, feature_cols, X, y, desc)
    else:
        print("Using separate CSVs: ENB2012_Heating_Load.csv, ENB2012_Cooling_Load.csv")
        for out_name, _, desc in OUT_DATASETS:
            csv_name = f"ENB2012_{'Heating' if 'heating' in out_name else 'Cooling'}_Load.csv"
            csv_path = os.path.join(DATA_ENB, csv_name)
            df = pd.read_csv(csv_path)
            feature_cols = [c for c in df.columns if c != "target"]
            y = df["target"].values
            out_dir = os.path.join(SRB, out_name)
            write_tsvgz_and_metadata(out_dir, out_name, feature_cols, df[feature_cols], y, desc)

    print("=" * 60)
    print("Conversion complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()

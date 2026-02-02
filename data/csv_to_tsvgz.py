"""Convert ENB CSVs to TSV.GZ in SRBench layout. Stdlib only."""
import csv
import gzip
import os

SRB = os.path.dirname(os.path.abspath(__file__))
DATA_ENB = os.path.join(SRB, "data_enb")
OUT = [
    ("enb_cooling", "ENB2012_Cooling_Load.csv"),
    ("enb_heating", "ENB2012_Heating_Load.csv"),
]

for name, csv_name in OUT:
    csv_path = os.path.join(DATA_ENB, csv_name)
    out_dir = os.path.join(SRB, name)
    os.makedirs(out_dir, exist_ok=True)
    tsv_gz_path = os.path.join(out_dir, name + ".tsv.gz")
    with open(csv_path, "r", encoding="utf-8") as f_in:
        reader = csv.reader(f_in)
        rows = list(reader)
    with gzip.open(tsv_gz_path, "wt", encoding="utf-8") as f_out:
        w = csv.writer(f_out, delimiter="\t")
        w.writerows(rows)
    print("Created", tsv_gz_path, "rows", len(rows) - 1)

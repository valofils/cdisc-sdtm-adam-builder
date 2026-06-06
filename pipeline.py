"""
CDISC SDTM & ADaM Builder — Main Pipeline
==========================================
Orchestrates the full pipeline:
  1. Generate synthetic raw data
  2. Map to SDTM domains (DM, AE, VS, LB, EX, CM)
  3. Build ADaM datasets (ADSL, ADAE, ADLB)
  4. Run validation checks
  5. Export datasets + define.xml

Usage:
    python pipeline.py
    python pipeline.py --output-dir /path/to/output
"""

import argparse
import os
import pandas as pd
from pathlib import Path

# Raw data
from src.utils.synthetic_data import generate_all

# SDTM mappers
from src.sdtm.dm import map_dm
from src.sdtm.ae import map_ae
from src.sdtm.vs import map_vs
from src.sdtm.lb import map_lb
from src.sdtm.ex_cm import map_ex, map_cm

# ADaM builders
from src.adam.adsl import build_adsl
from src.adam.adae import build_adae
from src.adam.adlb import build_adlb

# Validation
from src.validation.checks import run_all_checks

# define.xml
from src.utils.define_xml import generate_define_xml


def run_pipeline(output_dir: str = ".") -> None:
    sdtm_dir = os.path.join(output_dir, "data", "sdtm")
    adam_dir = os.path.join(output_dir, "data", "adam")
    out_dir  = os.path.join(output_dir, "outputs")
    os.makedirs(sdtm_dir, exist_ok=True)
    os.makedirs(adam_dir, exist_ok=True)
    os.makedirs(out_dir,  exist_ok=True)

    print("=" * 60)
    print("  CDISC SDTM & ADaM Builder — Pipeline Start")
    print("=" * 60)

    # ── Step 1: Raw data ───────────────────────────────────────────
    print("\n[1/5] Generating synthetic raw data ...")
    raw = generate_all(os.path.join(output_dir, "data", "raw"))

    # ── Step 2: SDTM mapping ───────────────────────────────────────
    print("\n[2/5] Mapping to SDTM domains ...")

    dm = map_dm(raw["dm_raw"])
    ae = map_ae(raw["ae_raw"], dm)
    vs = map_vs(raw["vs_raw"], dm)
    lb = map_lb(raw["lb_raw"], dm)
    ex = map_ex(raw["ex_raw"], dm)
    cm = map_cm(raw["cm_raw"], dm)

    sdtm = {"DM": dm, "AE": ae, "VS": vs, "LB": lb, "EX": ex, "CM": cm}
    for name, df in sdtm.items():
        path = os.path.join(sdtm_dir, f"{name.lower()}.csv")
        df.to_csv(path, index=False)
        print(f"    {name:4s}  {len(df):>6,} rows  → {path}")

    # ── Step 3: ADaM datasets ──────────────────────────────────────
    print("\n[3/5] Building ADaM datasets ...")

    adsl = build_adsl(dm, ex)
    adae = build_adae(ae, adsl)
    adlb = build_adlb(lb, adsl)

    adam = {"ADSL": adsl, "ADAE": adae, "ADLB": adlb}
    for name, df in adam.items():
        path = os.path.join(adam_dir, f"{name.lower()}.csv")
        df.to_csv(path, index=False)
        print(f"    {name:4s}  {len(df):>6,} rows  → {path}")

    # ── Step 4: Validation ─────────────────────────────────────────
    print("\n[4/5] Running CDISC validation checks ...")
    findings = run_all_checks(dm, ae, vs, lb, adsl, adae, adlb)

    findings_path = os.path.join(out_dir, "validation_findings.csv")
    findings.to_csv(findings_path, index=False)
    print(f"    Findings report → {findings_path}")

    # ── Step 5: define.xml ─────────────────────────────────────────
    print("\n[5/5] Generating define.xml ...")
    all_ds = {**sdtm, **adam}
    generate_define_xml(all_ds, os.path.join(out_dir, "define.xml"))

    # ── Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Pipeline Complete — Summary")
    print("=" * 60)
    total_rows = sum(len(d) for d in all_ds.values())
    print(f"  Datasets  : {len(all_ds)} ({len(sdtm)} SDTM + {len(adam)} ADaM)")
    print(f"  Records   : {total_rows:,} total rows")
    errors = (findings["severity"] == "ERROR").sum() if len(findings) else 0
    warns  = (findings["severity"] == "WARNING").sum() if len(findings) else 0
    print(f"  Validation: {errors} errors, {warns} warnings")
    print(f"  Outputs   : {out_dir}/")
    print("=" * 60)

    return all_ds, findings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CDISC SDTM & ADaM Builder")
    parser.add_argument("--output-dir", default=".", help="Root output directory")
    args = parser.parse_args()
    run_pipeline(args.output_dir)

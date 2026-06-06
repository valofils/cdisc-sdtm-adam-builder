"""
CDISC Validation Checks
Implements a subset of Pinnacle 21 Community rules for SDTM and ADaM.
Each check returns a list of finding dicts: {rule, dataset, variable, usubjid, message, severity}.
"""

from __future__ import annotations
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import Callable


@dataclass
class Finding:
    rule: str
    dataset: str
    variable: str
    usubjid: str
    message: str
    severity: str  # ERROR | WARNING | INFO


def _findings_df(findings: list[Finding]) -> pd.DataFrame:
    if not findings:
        return pd.DataFrame(columns=["rule", "dataset", "variable", "usubjid", "message", "severity"])
    return pd.DataFrame([asdict(f) for f in findings])


# ── SDTM checks ───────────────────────────────────────────────────────────────

def check_sdtm001_required_vars(dm: pd.DataFrame) -> list[Finding]:
    """SD0001 — Required DM variables must be present."""
    required = ["STUDYID", "DOMAIN", "USUBJID", "SUBJID", "SITEID",
                "RFSTDTC", "AGE", "AGEU", "SEX", "RACE", "COUNTRY",
                "ARMCD", "ARM"]
    findings = []
    for var in required:
        if var not in dm.columns:
            findings.append(Finding(
                rule="SD0001", dataset="DM", variable=var, usubjid="ALL",
                message=f"Required variable {var} is missing from DM domain.",
                severity="ERROR"
            ))
    return findings


def check_sdtm002_usubjid_unique(dm: pd.DataFrame) -> list[Finding]:
    """SD0002 — USUBJID must be unique within DM."""
    dups = dm[dm.duplicated("USUBJID", keep=False)]["USUBJID"].unique()
    return [
        Finding("SD0002", "DM", "USUBJID", uid,
                f"Duplicate USUBJID '{uid}' found in DM.", "ERROR")
        for uid in dups
    ]


def check_sdtm003_sex_ct(dm: pd.DataFrame) -> list[Finding]:
    """SD0003 — SEX must use controlled terminology (M/F/U/UNDIFFERENTIATED)."""
    valid = {"M", "F", "U", "UNDIFFERENTIATED"}
    bad = dm[~dm["SEX"].isin(valid)]
    return [
        Finding("SD0003", "DM", "SEX", row["USUBJID"],
                f"Invalid SEX value '{row['SEX']}'.", "ERROR")
        for _, row in bad.iterrows()
    ]


def check_sdtm004_dates_iso8601(df: pd.DataFrame, domain: str, date_cols: list[str]) -> list[Finding]:
    """SD0004 — Date variables must be in ISO 8601 format (YYYY-MM-DD or partial)."""
    findings = []
    for col in date_cols:
        if col not in df.columns:
            continue
        non_null = df[col].dropna()
        try:
            pd.to_datetime(non_null, format="%Y-%m-%d")
        except Exception:
            bad = df[pd.to_datetime(df[col], errors="coerce").isna() & df[col].notna()]
            for _, row in bad.iterrows():
                findings.append(Finding(
                    "SD0004", domain, col,
                    row.get("USUBJID", "?"),
                    f"{col} value '{row[col]}' is not valid ISO 8601.",
                    "ERROR"
                ))
    return findings


def check_sdtm005_aeser_ct(ae: pd.DataFrame) -> list[Finding]:
    """SD0005 — AESER must be Y or N."""
    valid = {"Y", "N"}
    bad = ae[~ae["AESER"].isin(valid)]
    return [
        Finding("SD0005", "AE", "AESER", row["USUBJID"],
                f"Invalid AESER value '{row['AESER']}'.", "ERROR")
        for _, row in bad.iterrows()
    ]


def check_sdtm006_ae_start_before_end(ae: pd.DataFrame) -> list[Finding]:
    """SD0006 — AESTDTC must be <= AEENDTC."""
    bad = ae[pd.to_datetime(ae["AESTDTC"]) > pd.to_datetime(ae["AEENDTC"])]
    return [
        Finding("SD0006", "AE", "AESTDTC/AEENDTC", row["USUBJID"],
                f"AE seq {row['AESEQ']}: start date {row['AESTDTC']} is after end date {row['AEENDTC']}.",
                "ERROR")
        for _, row in bad.iterrows()
    ]


def check_sdtm007_seq_within_subject(df: pd.DataFrame, domain: str, seq_col: str) -> list[Finding]:
    """SD0007 — Sequence variable must be unique within USUBJID."""
    findings = []
    dups = df[df.duplicated(["USUBJID", seq_col], keep=False)]
    for uid in dups["USUBJID"].unique():
        findings.append(Finding(
            "SD0007", domain, seq_col, uid,
            f"Duplicate {seq_col} values found for {uid} in {domain}.",
            "ERROR"
        ))
    return findings


# ── ADaM checks ───────────────────────────────────────────────────────────────

def check_adam001_adsl_required_vars(adsl: pd.DataFrame) -> list[Finding]:
    """AD0001 — ADSL required variables."""
    required = ["STUDYID", "USUBJID", "SUBJID", "SITEID",
                "TRT01P", "TRT01PN", "TRT01A", "TRT01AN",
                "SAFFL", "AGE", "SEX", "RACE"]
    findings = []
    for var in required:
        if var not in adsl.columns:
            findings.append(Finding(
                "AD0001", "ADSL", var, "ALL",
                f"Required ADSL variable {var} is missing.", "ERROR"
            ))
    return findings


def check_adam002_saffl_ct(adsl: pd.DataFrame) -> list[Finding]:
    """AD0002 — Population flags must be Y or N."""
    flags = [c for c in ["SAFFL", "EFFFL", "ITTFL", "PPROTFL"] if c in adsl.columns]
    findings = []
    for flag in flags:
        bad = adsl[~adsl[flag].isin({"Y", "N", ""})]
        for _, row in bad.iterrows():
            findings.append(Finding(
                "AD0002", "ADSL", flag, row["USUBJID"],
                f"Invalid {flag} value '{row[flag]}'.", "ERROR"
            ))
    return findings


def check_adam003_adlb_base_not_null(adlb: pd.DataFrame) -> list[Finding]:
    """AD0003 — BASE must not be null for post-baseline records."""
    post = adlb[(adlb.get("ABLFL", "") != "Y") & adlb["BASE"].isna()]
    return [
        Finding("AD0003", "ADLB", "BASE", row["USUBJID"],
                f"BASE is null for post-baseline record: {row.get('PARAMCD', '')} visit {row.get('VISIT', '')}.",
                "WARNING")
        for _, row in post.iterrows()
    ]


def check_adam004_trtemfl(adae: pd.DataFrame) -> list[Finding]:
    """AD0004 — TRTEMFL should be present."""
    if "TRTEMFL" not in adae.columns:
        return [Finding("AD0004", "ADAE", "TRTEMFL", "ALL",
                        "TRTEMFL variable is missing from ADAE.", "ERROR")]
    return []


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_all_checks(
    dm: pd.DataFrame,
    ae: pd.DataFrame,
    vs: pd.DataFrame,
    lb: pd.DataFrame,
    adsl: pd.DataFrame,
    adae: pd.DataFrame,
    adlb: pd.DataFrame,
) -> pd.DataFrame:
    """Run all validation checks and return a consolidated findings DataFrame."""
    findings: list[Finding] = []

    # SDTM
    findings += check_sdtm001_required_vars(dm)
    findings += check_sdtm002_usubjid_unique(dm)
    findings += check_sdtm003_sex_ct(dm)
    findings += check_sdtm004_dates_iso8601(dm, "DM", ["RFSTDTC", "BRTHDTC", "RFICDTC"])
    findings += check_sdtm004_dates_iso8601(ae, "AE", ["AESTDTC", "AEENDTC"])
    findings += check_sdtm005_aeser_ct(ae)
    findings += check_sdtm006_ae_start_before_end(ae)
    findings += check_sdtm007_seq_within_subject(ae, "AE", "AESEQ")
    findings += check_sdtm007_seq_within_subject(vs, "VS", "VSSEQ")

    # ADaM
    findings += check_adam001_adsl_required_vars(adsl)
    findings += check_adam002_saffl_ct(adsl)
    findings += check_adam003_adlb_base_not_null(adlb)
    findings += check_adam004_trtemfl(adae)

    result = _findings_df(findings)
    errors   = (result["severity"] == "ERROR").sum()
    warnings = (result["severity"] == "WARNING").sum()
    print(f"[Validation] {len(result)} findings — {errors} errors, {warnings} warnings")
    return result

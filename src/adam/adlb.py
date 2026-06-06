"""
ADaM Dataset: ADLB — Laboratory Analysis Dataset
CDISC ADaM BDS (Basic Data Structure) Implementation Guide v1.3
Derived from SDTM LB + ADSL.
"""

import pandas as pd


def build_adlb(lb: pd.DataFrame, adsl: pd.DataFrame) -> pd.DataFrame:
    """
    Build ADLB from SDTM LB and ADaM ADSL.

    BDS structure: one record per subject per parameter per visit.
    Key additions:
      - BASE    : baseline value
      - CHG     : change from baseline
      - PCHG    : percent change from baseline
      - BNRIND  : baseline reference range indicator
      - SHIFT   : shift from baseline (e.g. NORMAL→HIGH)
    """
    adlb = lb.copy()

    # Join treatment info from ADSL
    adsl_cols = [
        "USUBJID", "TRT01A", "TRT01AN", "TRT01P", "TRT01PN",
        "SAFFL", "AGEGR1", "SEX",
    ]
    adlb = adlb.merge(adsl[adsl_cols], on="USUBJID", how="left")

    # Rename for ADaM BDS
    adlb = adlb.rename(columns={
        "LBTESTCD": "PARAMCD",
        "LBTEST":   "PARAM",
        "LBSTRESN": "AVAL",
        "LBSTRESC": "AVALC",
        "LBSTRESU": "AVALU",
        "LBSTNRLO": "ANRLO",
        "LBSTNRHI": "ANRHI",
        "LBNRIND":  "ANRIND",
        "LBBLFL":   "ABLFL",
        "LBDTC":    "ADT",
        "LBDY":     "ADY",
        "LBSEQ":    "LBSEQ",
    })

    adlb["PARAMN"] = adlb["PARAMCD"].astype("category").cat.codes + 1

    # Compute baseline per subject-parameter
    baseline = (
        adlb[adlb["ABLFL"] == "Y"]
        .groupby(["USUBJID", "PARAMCD"])["AVAL"]
        .first()
        .rename("BASE")
        .reset_index()
    )
    adlb = adlb.merge(baseline, on=["USUBJID", "PARAMCD"], how="left")

    adlb["CHG"]  = adlb["AVAL"] - adlb["BASE"]
    adlb["PCHG"] = (adlb["CHG"] / adlb["BASE"].replace(0, float("nan")) * 100).round(2)

    # Baseline reference range indicator
    bnrind = (
        adlb[adlb["ABLFL"] == "Y"][["USUBJID", "PARAMCD", "ANRIND"]]
        .rename(columns={"ANRIND": "BNRIND"})
    )
    adlb = adlb.merge(bnrind, on=["USUBJID", "PARAMCD"], how="left")

    # Shift from baseline normal range
    adlb["SHIFT1"] = adlb["BNRIND"].fillna("") + "→" + adlb["ANRIND"].fillna("")

    col_order = [
        "STUDYID", "USUBJID", "LBSEQ",
        "TRT01A", "TRT01AN", "TRT01P", "TRT01PN",
        "PARAMCD", "PARAM", "PARAMN",
        "AVAL", "AVALC", "AVALU",
        "BASE", "CHG", "PCHG",
        "ANRLO", "ANRHI", "ANRIND", "BNRIND", "SHIFT1",
        "ABLFL", "VISIT", "VISITNUM", "ADT", "ADY",
        "SAFFL", "AGEGR1", "SEX",
    ]
    return adlb[[c for c in col_order if c in adlb.columns]].reset_index(drop=True)

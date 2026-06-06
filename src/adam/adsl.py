"""
ADaM Dataset: ADSL — Subject-Level Analysis Dataset
CDISC ADaM Implementation Guide v1.3
Derived from SDTM DM + EX domains.
"""

import pandas as pd
from datetime import date

STUDY_ID = "CDISCPILOT01"


def build_adsl(dm: pd.DataFrame, ex: pd.DataFrame) -> pd.DataFrame:
    """
    Build ADSL from SDTM DM and EX.

    Key ADaM additions over DM:
      - TRT01P / TRT01A  : planned / actual treatment
      - TRTSDT / TRTEDTC : treatment start/end dates
      - SAFFL / EFFFL    : safety / efficacy population flags
      - AGEGRxN          : analysis age group numeric
      - DURDIS           : duration of disease (simulated)
    """
    adsl = dm.copy()

    # Treatment variables
    arm_label = {"A": "Active Drug 100mg", "B": "Placebo"}
    adsl["TRT01P"]  = adsl["ARMCD"].map(arm_label)
    adsl["TRT01A"]  = adsl["TRT01P"]
    adsl["TRT01PN"] = adsl["ARMCD"].map({"A": 1, "B": 2})
    adsl["TRT01AN"] = adsl["TRT01PN"]

    # Treatment dates from EX
    ex_start = ex.groupby("USUBJID")["EXSTDTC"].min().rename("TRTSDT")
    ex_end   = ex.groupby("USUBJID")["EXENDTC"].max().rename("TRTEDTC")
    adsl = adsl.join(ex_start, on="USUBJID").join(ex_end, on="USUBJID")

    adsl["TRTDURD"] = (
        pd.to_datetime(adsl["TRTEDTC"]) - pd.to_datetime(adsl["TRTSDT"])
    ).dt.days + 1

    # Population flags — all enrolled are safety population
    adsl["SAFFL"]  = "Y"
    adsl["EFFFL"]  = "Y"
    adsl["ITTFL"]  = "Y"
    adsl["PPROTFL"] = "Y"

    # Age groups
    adsl["AGEGR1"] = pd.cut(
        adsl["AGE"],
        bins=[0, 50, 65, 200],
        labels=["<50", "50-65", ">65"],
        right=True
    ).astype(str)
    adsl["AGEGR1N"] = adsl["AGEGR1"].map({"<50": 1, "50-65": 2, ">65": 3})

    # Sex numeric
    adsl["SEXN"] = adsl["SEX"].map({"M": 1, "F": 2})

    # Race numeric
    race_map = {
        "WHITE": 1,
        "BLACK OR AFRICAN AMERICAN": 2,
        "ASIAN": 3,
        "OTHER": 4,
    }
    adsl["RACEN"] = adsl["RACE"].map(race_map)

    # Simulated baseline characteristics
    import numpy as np
    rng = np.random.default_rng(seed=42)
    n = len(adsl)
    adsl["BMIBL"]   = rng.normal(27, 4, n).round(1)
    adsl["HEIGHTBL"] = rng.normal(170, 10, n).round(1)
    adsl["WEIGHTBL"] = rng.normal(80, 15, n).round(1)
    adsl["DURDIS"]   = rng.integers(1, 120, n)      # months since diagnosis

    col_order = [
        "STUDYID", "USUBJID", "SUBJID", "SITEID",
        "RFSTDTC", "RFENDTC", "RFICDTC", "BRTHDTC",
        "AGE", "AGEU", "AGEGR1", "AGEGR1N",
        "SEX", "SEXN", "RACE", "RACEN", "ETHNIC", "COUNTRY",
        "ARMCD", "ARM", "ACTARMCD", "ACTARM",
        "TRT01P", "TRT01PN", "TRT01A", "TRT01AN",
        "TRTSDT", "TRTEDTC", "TRTDURD",
        "SAFFL", "EFFFL", "ITTFL", "PPROTFL",
        "BMIBL", "HEIGHTBL", "WEIGHTBL", "DURDIS",
    ]
    return adsl[[c for c in col_order if c in adsl.columns]].reset_index(drop=True)

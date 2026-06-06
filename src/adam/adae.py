"""
ADaM Dataset: ADAE — Adverse Events Analysis Dataset
CDISC ADaM Implementation Guide v1.3
Derived from SDTM AE + ADSL.
"""

import pandas as pd


def build_adae(ae: pd.DataFrame, adsl: pd.DataFrame) -> pd.DataFrame:
    """
    Build ADAE from SDTM AE and ADaM ADSL.

    Key ADaM additions:
      - Treatment variables joined from ADSL
      - AETOXGRN : numeric toxicity grade
      - TRTEMFL  : treatment-emergent AE flag
      - AESEVN   : numeric severity
    """
    adae = ae.copy()

    # Join treatment info from ADSL
    adsl_cols = [
        "USUBJID", "TRT01A", "TRT01AN", "TRT01P", "TRT01PN",
        "TRTSDT", "SAFFL", "AGEGR1", "SEX", "RACE",
    ]
    adae = adae.merge(adsl[adsl_cols], on="USUBJID", how="left")

    # Treatment-emergent flag: AE starts on or after first dose
    adae["TRTEMFL"] = (
        pd.to_datetime(adae["AESTDTC"]) >= pd.to_datetime(adae["TRTSDT"])
    ).map({True: "Y", False: ""})

    # Numeric severity
    sev_map = {"MILD": 1, "MODERATE": 2, "SEVERE": 3}
    adae["AESEVN"] = adae["AESEV"].map(sev_map)

    # Numeric toxicity grade (already string in SDTM)
    adae["AETOXGRN"] = pd.to_numeric(adae["AETOXGR"], errors="coerce")

    # Serious AE numeric flag
    adae["AESERN"] = (adae["AESER"] == "Y").astype(int)

    # Related AE flag numeric
    adae["AERELN"] = (adae["AEREL"] == "Y").astype(int)

    col_order = [
        "STUDYID", "USUBJID", "AESEQ",
        "TRT01A", "TRT01AN", "TRT01P", "TRT01PN",
        "AETERM", "AEDECOD", "AEBODSYS",
        "AESEV", "AESEVN", "AESER", "AESERN",
        "AEREL", "AERELN", "AEACN",
        "AETOXGR", "AETOXGRN",
        "AESTDTC", "AEENDTC", "AESTDY",
        "AEOUT", "TRTEMFL", "SAFFL",
        "AGEGR1", "SEX", "RACE",
    ]
    return adae[[c for c in col_order if c in adae.columns]].reset_index(drop=True)

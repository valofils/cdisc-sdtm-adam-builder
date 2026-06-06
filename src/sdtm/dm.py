"""
SDTM Domain: DM — Demographics
CDISC SDTM Implementation Guide v3.3
Maps raw subject-level data to SDTM DM domain structure.
"""

import pandas as pd
from datetime import date


STUDY_ID = "CDISCPILOT01"
DOMAIN = "DM"


def map_dm(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Map raw demographics to CDISC SDTM DM domain.

    Required variables: STUDYID, DOMAIN, USUBJID, SUBJID, SITEID, RFSTDTC,
                        AGE, AGEU, SEX, RACE, ETHNIC, COUNTRY, ARMCD, ARM,
                        ACTARMCD, ACTARM, DMDTC, DMDY
    """
    today = date.today().isoformat()
    dm = raw.copy().reset_index(drop=True)

    dm["STUDYID"] = STUDY_ID
    dm["DOMAIN"]  = DOMAIN
    dm["USUBJID"] = STUDY_ID + "-" + raw["subject_id"]
    dm["SUBJID"] = raw["subject_id"].str.split("-").str[1]
    dm["SITEID"] = raw["site_id"]
    dm["RFSTDTC"] = raw["enrollment_date"]              # Reference start date (first dose)
    dm["RFENDTC"] = pd.NaT                              # Placeholder — set by EX merge
    dm["RFICDTC"] = raw["consent_date"]                 # Informed consent date

    dm["BRTHDTC"] = raw["date_of_birth"]
    dm["AGE"] = (
        pd.to_datetime(raw["enrollment_date"]).dt.year
        - pd.to_datetime(raw["date_of_birth"]).dt.year
    )
    dm["AGEU"] = "YEARS"

    dm["SEX"] = raw["sex"]
    dm["RACE"] = raw["race"]
    dm["ETHNIC"] = raw["ethnicity"]
    dm["COUNTRY"] = raw["country"]

    arm_map = {"A": "Active Drug 100mg", "B": "Placebo"}
    dm["ARMCD"] = raw["treatment_arm"]
    dm["ARM"] = raw["treatment_arm"].map(arm_map)
    dm["ACTARMCD"] = dm["ARMCD"]
    dm["ACTARM"] = dm["ARM"]

    dm["DMDTC"] = raw["consent_date"]
    dm["DMDY"] = 1

    # Controlled terminology
    dm["DTHFL"] = ""         # Death flag — not populated for this study

    col_order = [
        "STUDYID", "DOMAIN", "USUBJID", "SUBJID", "SITEID",
        "RFSTDTC", "RFENDTC", "RFICDTC", "BRTHDTC",
        "AGE", "AGEU", "SEX", "RACE", "ETHNIC", "COUNTRY",
        "ARMCD", "ARM", "ACTARMCD", "ACTARM",
        "DMDTC", "DMDY", "DTHFL",
    ]
    return dm[col_order].reset_index(drop=True)

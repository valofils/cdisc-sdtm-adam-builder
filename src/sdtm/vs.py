"""
SDTM Domain: VS — Vital Signs
CDISC SDTM Implementation Guide v3.3
"""

import pandas as pd

STUDY_ID = "CDISCPILOT01"
DOMAIN = "VS"

TEST_MAP = {
    "systolic_bp":  ("SYSBP",  "Systolic Blood Pressure",  "mmHg"),
    "diastolic_bp": ("DIABP",  "Diastolic Blood Pressure", "mmHg"),
    "heart_rate":   ("PULSE",  "Pulse Rate",               "beats/min"),
    "temperature":  ("TEMP",   "Temperature",              "C"),
    "weight_kg":    ("WEIGHT", "Weight",                   "kg"),
    "height_cm":    ("HEIGHT", "Height",                   "cm"),
}

VISIT_DAY = {
    "SCREENING": -7,
    "DAY 1":     1,
    "WEEK 4":    28,
    "WEEK 8":    56,
    "WEEK 12":   84,
}


def map_vs(raw_vs: pd.DataFrame, dm: pd.DataFrame) -> pd.DataFrame:
    """
    Map raw vital signs to CDISC SDTM VS domain (vertical/unpivoted structure).
    Each test becomes its own row — standard SDTM general observations class.
    """
    rfstdtc_map = dm.set_index("USUBJID")["RFSTDTC"].to_dict()

    test_cols = list(TEST_MAP.keys())
    id_cols = ["subject_id", "visit", "visit_day", "vs_date"]

    melted = raw_vs[id_cols + test_cols].melt(
        id_vars=id_cols, var_name="raw_test", value_name="VSSTRESN"
    ).dropna(subset=["VSSTRESN"])

    vs = pd.DataFrame()
    vs["STUDYID"] = STUDY_ID
    vs["DOMAIN"] = DOMAIN
    vs["USUBJID"] = STUDY_ID + "-" + melted["subject_id"]

    vs["VSTESTCD"] = melted["raw_test"].map(lambda t: TEST_MAP[t][0])
    vs["VSTEST"]   = melted["raw_test"].map(lambda t: TEST_MAP[t][1])
    vs["VSSTRESU"] = melted["raw_test"].map(lambda t: TEST_MAP[t][2])
    vs["VSSTRESN"] = melted["VSSTRESN"].round(2)
    vs["VSSTRESC"]  = vs["VSSTRESN"].astype(str)
    vs["VSORRES"]   = vs["VSSTRESC"]
    vs["VSORRESU"]  = vs["VSSTRESU"]

    vs["VISIT"]   = melted["visit"]
    vs["VISITNUM"] = melted["visit"].map({v: i+1 for i, v in enumerate(VISIT_DAY)})
    vs["VSDTC"]   = melted["vs_date"]

    rfstdtc = vs["USUBJID"].map(rfstdtc_map)
    delta = (pd.to_datetime(melted["vs_date"].values) - pd.to_datetime(rfstdtc.values)).days
    vs["VSDY"] = [d + 1 if d >= 0 else d for d in delta]

    vs["VSBLFL"] = (melted["visit"] == "SCREENING").map({True: "Y", False: ""})

    vs["VSSEQ"] = vs.groupby("USUBJID").cumcount() + 1

    col_order = [
        "STUDYID", "DOMAIN", "USUBJID", "VSSEQ",
        "VSTESTCD", "VSTEST", "VSORRES", "VSORRESU",
        "VSSTRESC", "VSSTRESN", "VSSTRESU",
        "VSBLFL", "VISIT", "VISITNUM", "VSDTC", "VSDY",
    ]
    return vs[col_order].reset_index(drop=True)

"""
SDTM Domain: LB — Laboratory Test Results
CDISC SDTM Implementation Guide v3.3
"""

import pandas as pd

STUDY_ID = "CDISCPILOT01"
DOMAIN = "LB"

TEST_CODES = {
    "ALT":         "ALT",
    "AST":         "AST",
    "Creatinine":  "CREAT",
    "Haemoglobin": "HGB",
    "Platelets":   "PLAT",
    "WBC":         "WBC",
    "Glucose":     "GLUC",
}

VISIT_DAY = {"SCREENING": -7, "WEEK 4": 28, "WEEK 12": 84}


def map_lb(raw_lb: pd.DataFrame, dm: pd.DataFrame) -> pd.DataFrame:
    """Map raw lab results to CDISC SDTM LB domain."""
    rfstdtc_map = dm.set_index("USUBJID")["RFSTDTC"].to_dict()

    lb = pd.DataFrame()
    lb["STUDYID"]  = STUDY_ID
    lb["DOMAIN"]   = DOMAIN
    lb["USUBJID"]  = STUDY_ID + "-" + raw_lb["subject_id"]
    lb["LBSEQ"]    = raw_lb.groupby("subject_id").cumcount() + 1

    lb["LBTESTCD"] = raw_lb["lb_test"].map(TEST_CODES)
    lb["LBTEST"]   = raw_lb["lb_test"]
    lb["LBCAT"]    = "CHEMISTRY"

    lb["LBORRES"]  = raw_lb["lb_result"].astype(str)
    lb["LBORRESU"] = raw_lb["lb_unit"]
    lb["LBSTRESN"] = raw_lb["lb_result"]
    lb["LBSTRESC"] = lb["LBSTRESN"].astype(str)
    lb["LBSTRESU"] = raw_lb["lb_unit"]

    lb["LBSTNRLO"] = raw_lb["lb_ref_lo"]
    lb["LBSTNRHI"] = raw_lb["lb_ref_hi"]
    lb["LBNRIND"]  = raw_lb["lb_nrind"]

    lb["VISIT"]    = raw_lb["visit"]
    lb["VISITNUM"] = raw_lb["visit"].map({v: i+1 for i, v in enumerate(VISIT_DAY)})
    lb["LBDTC"]    = raw_lb["lb_date"]

    rfstdtc = lb["USUBJID"].map(rfstdtc_map)
    delta = (pd.to_datetime(raw_lb["lb_date"].values) - pd.to_datetime(rfstdtc.values)).days
    lb["LBDY"] = [d + 1 if d >= 0 else d for d in delta]

    lb["LBBLFL"] = (raw_lb["visit"] == "SCREENING").map({True: "Y", False: ""})

    col_order = [
        "STUDYID", "DOMAIN", "USUBJID", "LBSEQ",
        "LBTESTCD", "LBTEST", "LBCAT",
        "LBORRES", "LBORRESU", "LBSTRESC", "LBSTRESN", "LBSTRESU",
        "LBSTNRLO", "LBSTNRHI", "LBNRIND", "LBBLFL",
        "VISIT", "VISITNUM", "LBDTC", "LBDY",
    ]
    return lb[col_order].reset_index(drop=True)

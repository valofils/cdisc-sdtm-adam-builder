"""
SDTM Domains: EX (Exposure) and CM (Concomitant Medications)
CDISC SDTM Implementation Guide v3.3
"""

import pandas as pd

STUDY_ID = "CDISCPILOT01"


def map_ex(raw_ex: pd.DataFrame, dm: pd.DataFrame) -> pd.DataFrame:
    """Map raw exposure records to CDISC SDTM EX domain."""
    rfstdtc_map = dm.set_index("USUBJID")["RFSTDTC"].to_dict()

    ex = pd.DataFrame()
    ex["STUDYID"]  = STUDY_ID
    ex["DOMAIN"]   = "EX"
    ex["USUBJID"]  = STUDY_ID + "-" + raw_ex["subject_id"]
    ex["EXSEQ"]    = raw_ex.groupby("subject_id").cumcount() + 1

    ex["EXTRT"]    = raw_ex["ex_trt"]
    ex["EXDOSE"]   = raw_ex["ex_dose"]
    ex["EXDOSU"]   = raw_ex["ex_dose_unit"]
    ex["EXROUTE"]  = raw_ex["ex_route"]
    ex["EXDOSFRQ"] = "QD"                    # Once daily

    ex["EXSTDTC"]  = raw_ex["ex_start_date"]
    ex["EXENDTC"]  = raw_ex["ex_end_date"]

    rfstdtc = ex["USUBJID"].map(rfstdtc_map)
    delta = (pd.to_datetime(raw_ex["ex_start_date"].values) - pd.to_datetime(rfstdtc.values)).days
    ex["EXSTDY"] = [d + 1 if d >= 0 else d for d in delta]

    col_order = [
        "STUDYID", "DOMAIN", "USUBJID", "EXSEQ",
        "EXTRT", "EXDOSE", "EXDOSU", "EXROUTE", "EXDOSFRQ",
        "EXSTDTC", "EXENDTC", "EXSTDY",
    ]
    return ex[col_order].reset_index(drop=True)


def map_cm(raw_cm: pd.DataFrame, dm: pd.DataFrame) -> pd.DataFrame:
    """Map raw concomitant medications to CDISC SDTM CM domain."""
    rfstdtc_map = dm.set_index("USUBJID")["RFSTDTC"].to_dict()

    cm = pd.DataFrame()
    cm["STUDYID"]  = STUDY_ID
    cm["DOMAIN"]   = "CM"
    cm["USUBJID"]  = STUDY_ID + "-" + raw_cm["subject_id"]
    cm["CMSEQ"]    = raw_cm.groupby("subject_id").cumcount() + 1

    cm["CMTRT"]    = raw_cm["cm_term"].str.upper()
    cm["CMDECOD"]  = raw_cm["cm_generic"]
    cm["CMATC"]    = raw_cm["cm_atc_class"]
    cm["CMROUTE"]  = "ORAL"
    cm["CMINDC"]   = raw_cm["cm_indication"]
    cm["CMENRF"]   = raw_cm["cm_ongoing"]

    cm["CMSTDTC"]  = raw_cm["cm_start_date"]
    cm["CMENDTC"]  = raw_cm["cm_end_date"]

    rfstdtc = cm["USUBJID"].map(rfstdtc_map)
    delta = (pd.to_datetime(raw_cm["cm_start_date"].values) - pd.to_datetime(rfstdtc.values)).days
    cm["CMSTDY"] = [d + 1 if d >= 0 else d for d in delta]

    col_order = [
        "STUDYID", "DOMAIN", "USUBJID", "CMSEQ",
        "CMTRT", "CMDECOD", "CMATC", "CMROUTE",
        "CMINDC", "CMENRF",
        "CMSTDTC", "CMENDTC", "CMSTDY",
    ]
    return cm[col_order].reset_index(drop=True)

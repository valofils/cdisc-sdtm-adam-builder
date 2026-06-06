"""
SDTM Domain: AE — Adverse Events
CDISC SDTM Implementation Guide v3.3
"""

import pandas as pd

STUDY_ID = "CDISCPILOT01"
DOMAIN = "AE"


def map_ae(raw_ae: pd.DataFrame, dm: pd.DataFrame) -> pd.DataFrame:
    """
    Map raw AE data to CDISC SDTM AE domain.

    Required: STUDYID, DOMAIN, USUBJID, AESEQ, AETERM, AEDECOD, AEBODSYS,
              AESEV, AESER, AEREL, AESTDTC, AEENDTC, AEOUT, AEACN
    """
    usubjid_map = dict(zip(
        dm["USUBJID"].str.replace(STUDY_ID + "-", "", regex=False),
        dm["USUBJID"]
    ))
    rfstdtc_map = dm.set_index("USUBJID")["RFSTDTC"].to_dict()

    ae = pd.DataFrame()
    ae["STUDYID"] = STUDY_ID
    ae["DOMAIN"] = DOMAIN
    ae["USUBJID"] = STUDY_ID + "-" + raw_ae["subject_id"]
    ae["AESEQ"] = raw_ae.groupby("subject_id").cumcount() + 1

    ae["AETERM"] = raw_ae["ae_term"].str.upper()
    ae["AEDECOD"] = raw_ae["ae_meddra_pt"]          # MedDRA preferred term
    ae["AEBODSYS"] = raw_ae["ae_soc"]               # System Organ Class
    ae["AESEV"] = raw_ae["ae_severity"]
    ae["AESER"] = raw_ae["ae_serious"]
    ae["AEREL"] = raw_ae["ae_related"]
    ae["AEACN"] = raw_ae["ae_action_taken"]

    ae["AESTDTC"] = raw_ae["ae_start_date"]
    ae["AEENDTC"] = raw_ae["ae_end_date"]

    # Calculate study day relative to RFSTDTC
    ae_start = pd.to_datetime(raw_ae["ae_start_date"])
    rfstdtc = ae["USUBJID"].map(rfstdtc_map)
    rfstdtc_dt = pd.to_datetime(rfstdtc)
    delta = (ae_start - rfstdtc_dt).dt.days
    ae["AESTDY"] = delta.apply(lambda d: d + 1 if d >= 0 else d)

    ae["AEOUT"] = "RECOVERED/RESOLVED"              # Simplified for synthetic data
    ae["AETOXGR"] = ae["AESEV"].map({
        "MILD": "1", "MODERATE": "2", "SEVERE": "3"
    })

    col_order = [
        "STUDYID", "DOMAIN", "USUBJID", "AESEQ",
        "AETERM", "AEDECOD", "AEBODSYS",
        "AESEV", "AESER", "AEREL", "AEACN",
        "AESTDTC", "AEENDTC", "AESTDY",
        "AEOUT", "AETOXGR",
    ]
    return ae[col_order].reset_index(drop=True)

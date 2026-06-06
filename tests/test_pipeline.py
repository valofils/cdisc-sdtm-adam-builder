"""
Unit Tests — CDISC SDTM & ADaM Builder
Run with: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
import numpy as np

from src.utils.synthetic_data import (
    generate_subjects, generate_adverse_events,
    generate_vital_signs, generate_lab_results,
    generate_exposure, generate_concomitant_meds,
)
from src.sdtm.dm import map_dm
from src.sdtm.ae import map_ae
from src.sdtm.vs import map_vs
from src.sdtm.lb import map_lb
from src.sdtm.ex_cm import map_ex, map_cm
from src.adam.adsl import build_adsl
from src.adam.adae import build_adae
from src.adam.adlb import build_adlb
from src.validation.checks import (
    check_sdtm001_required_vars,
    check_sdtm002_usubjid_unique,
    check_sdtm003_sex_ct,
    check_sdtm006_ae_start_before_end,
    check_adam001_adsl_required_vars,
    run_all_checks,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def raw():
    subjects = generate_subjects()
    return {
        "dm_raw": subjects,
        "ae_raw": generate_adverse_events(subjects),
        "vs_raw": generate_vital_signs(subjects),
        "lb_raw": generate_lab_results(subjects),
        "ex_raw": generate_exposure(subjects),
        "cm_raw": generate_concomitant_meds(subjects),
    }


@pytest.fixture(scope="module")
def sdtm(raw):
    dm = map_dm(raw["dm_raw"])
    ae = map_ae(raw["ae_raw"], dm)
    vs = map_vs(raw["vs_raw"], dm)
    lb = map_lb(raw["lb_raw"], dm)
    ex = map_ex(raw["ex_raw"], dm)
    cm = map_cm(raw["cm_raw"], dm)
    return {"dm": dm, "ae": ae, "vs": vs, "lb": lb, "ex": ex, "cm": cm}


@pytest.fixture(scope="module")
def adam(sdtm):
    adsl = build_adsl(sdtm["dm"], sdtm["ex"])
    adae = build_adae(sdtm["ae"], adsl)
    adlb = build_adlb(sdtm["lb"], adsl)
    return {"adsl": adsl, "adae": adae, "adlb": adlb}


# ── Synthetic data tests ───────────────────────────────────────────────────────

class TestSyntheticData:
    def test_subject_count(self, raw):
        assert len(raw["dm_raw"]) == 80

    def test_treatment_arms_balanced(self, raw):
        counts = raw["dm_raw"]["treatment_arm"].value_counts()
        assert set(counts.index) == {"A", "B"}

    def test_ae_has_subject_ids(self, raw):
        subj_ids = set(raw["dm_raw"]["subject_id"])
        ae_ids = set(raw["ae_raw"]["subject_id"])
        assert ae_ids.issubset(subj_ids)

    def test_vs_visit_count(self, raw):
        visits_per_subject = raw["vs_raw"].groupby("subject_id")["visit"].nunique()
        assert (visits_per_subject == 5).all()


# ── SDTM mapping tests ─────────────────────────────────────────────────────────

class TestSDTMDM:
    def test_required_columns(self, sdtm):
        required = ["STUDYID", "DOMAIN", "USUBJID", "SUBJID", "SITEID",
                    "AGE", "AGEU", "SEX", "RACE", "COUNTRY", "ARMCD", "ARM"]
        for col in required:
            assert col in sdtm["dm"].columns, f"Missing DM column: {col}"

    def test_domain_value(self, sdtm):
        assert (sdtm["dm"]["DOMAIN"] == "DM").all()

    def test_studyid_value(self, sdtm):
        assert (sdtm["dm"]["STUDYID"] == "CDISCPILOT01").all()

    def test_usubjid_unique(self, sdtm):
        assert sdtm["dm"]["USUBJID"].is_unique

    def test_age_positive(self, sdtm):
        assert (sdtm["dm"]["AGE"] > 0).all()

    def test_sex_valid(self, sdtm):
        assert sdtm["dm"]["SEX"].isin(["M", "F"]).all()

    def test_ageu_years(self, sdtm):
        assert (sdtm["dm"]["AGEU"] == "YEARS").all()


class TestSDTMAE:
    def test_required_columns(self, sdtm):
        for col in ["USUBJID", "AESEQ", "AETERM", "AEDECOD", "AEBODSYS",
                    "AESEV", "AESER", "AESTDTC", "AEENDTC"]:
            assert col in sdtm["ae"].columns

    def test_aeser_ct(self, sdtm):
        assert sdtm["ae"]["AESER"].isin(["Y", "N"]).all()

    def test_dates_chronological(self, sdtm):
        starts = pd.to_datetime(sdtm["ae"]["AESTDTC"])
        ends   = pd.to_datetime(sdtm["ae"]["AEENDTC"])
        assert (starts <= ends).all()

    def test_aestdy_relative(self, sdtm):
        assert sdtm["ae"]["AESTDY"].notna().all()


class TestSDTMVS:
    def test_vertical_structure(self, sdtm):
        codes = sdtm["vs"]["VSTESTCD"].unique()
        assert "SYSBP" in codes
        assert "DIABP" in codes
        assert "WEIGHT" in codes

    def test_no_negative_values(self, sdtm):
        assert (sdtm["vs"]["VSSTRESN"] > 0).all()


class TestSDTMLB:
    def test_baseline_flag(self, sdtm):
        blfl = sdtm["lb"][sdtm["lb"]["LBBLFL"] == "Y"]
        assert len(blfl) > 0

    def test_nrind_ct(self, sdtm):
        assert sdtm["lb"]["LBNRIND"].isin(["LOW", "NORMAL", "HIGH"]).all()


# ── ADaM tests ─────────────────────────────────────────────────────────────────

class TestADSL:
    def test_required_columns(self, adam):
        for col in ["USUBJID", "TRT01P", "TRT01PN", "TRT01A",
                    "SAFFL", "AGE", "SEX", "AGEGR1"]:
            assert col in adam["adsl"].columns

    def test_saffl_all_y(self, adam):
        assert (adam["adsl"]["SAFFL"] == "Y").all()

    def test_one_row_per_subject(self, adam):
        assert adam["adsl"]["USUBJID"].is_unique

    def test_trt_numeric(self, adam):
        assert adam["adsl"]["TRT01PN"].isin([1, 2]).all()

    def test_age_groups(self, adam):
        assert adam["adsl"]["AGEGR1"].isin(["<50", "50-65", ">65"]).all()


class TestADAE:
    def test_trtemfl_present(self, adam):
        assert "TRTEMFL" in adam["adae"].columns

    def test_aesevn_range(self, adam):
        assert adam["adae"]["AESEVN"].between(1, 3).all()

    def test_treatment_joined(self, adam):
        assert "TRT01A" in adam["adae"].columns
        assert adam["adae"]["TRT01A"].notna().all()


class TestADLB:
    def test_bds_structure(self, adam):
        for col in ["PARAMCD", "PARAM", "AVAL", "BASE", "CHG", "PCHG"]:
            assert col in adam["adlb"].columns

    def test_base_populated_for_baselines(self, adam):
        baselines = adam["adlb"][adam["adlb"]["ABLFL"] == "Y"]
        assert baselines["BASE"].notna().all()

    def test_chg_zero_at_baseline(self, adam):
        baselines = adam["adlb"][adam["adlb"]["ABLFL"] == "Y"]
        assert (baselines["CHG"].fillna(0) == 0).all()

    def test_shift_column_present(self, adam):
        assert "SHIFT1" in adam["adlb"].columns


# ── Validation check tests ─────────────────────────────────────────────────────

class TestValidation:
    def test_no_errors_on_clean_data(self, sdtm, adam):
        findings = run_all_checks(
            sdtm["dm"], sdtm["ae"], sdtm["vs"], sdtm["lb"],
            adam["adsl"], adam["adae"], adam["adlb"]
        )
        errors = findings[findings["severity"] == "ERROR"]
        assert len(errors) == 0, f"Unexpected errors:\n{errors.to_string()}"

    def test_catch_duplicate_usubjid(self, sdtm):
        dm_bad = pd.concat([sdtm["dm"].head(5), sdtm["dm"].head(3)])
        findings = check_sdtm002_usubjid_unique(dm_bad)
        assert len(findings) > 0

    def test_catch_bad_sex(self, sdtm):
        dm_bad = sdtm["dm"].copy()
        dm_bad.loc[0, "SEX"] = "UNKNOWN"
        findings = check_sdtm003_sex_ct(dm_bad)
        assert len(findings) == 1

    def test_catch_date_inversion(self, sdtm):
        ae_bad = sdtm["ae"].copy()
        ae_bad.loc[0, "AESTDTC"] = "2025-12-31"
        ae_bad.loc[0, "AEENDTC"] = "2025-01-01"
        findings = check_sdtm006_ae_start_before_end(ae_bad)
        assert len(findings) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

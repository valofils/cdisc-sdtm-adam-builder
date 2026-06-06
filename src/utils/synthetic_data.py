"""
Synthetic Clinical Trial Data Generator
Produces raw EDC-style data for a Phase II RCT (oncology / cardiovascular placeholder).
All data is entirely fictional and HIPAA-safe.
"""

import random
import numpy as np
import pandas as pd
from datetime import date, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

STUDY_ID = "CDISCPILOT01"
N_SUBJECTS = 80
TREATMENT_ARMS = {"A": "Active Drug 100mg", "B": "Placebo"}
SITES = ["001", "002", "003", "004"]
SEXES = ["M", "F"]
RACES = ["WHITE", "BLACK OR AFRICAN AMERICAN", "ASIAN", "OTHER"]
ETHNICITIES = ["HISPANIC OR LATINO", "NOT HISPANIC OR LATINO"]


def _rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_subjects() -> pd.DataFrame:
    """Raw subject-level demographic data (pre-SDTM)."""
    records = []
    for i in range(1, N_SUBJECTS + 1):
        site = random.choice(SITES)
        arm = random.choice(list(TREATMENT_ARMS.keys()))
        bday = _rand_date(date(1940, 1, 1), date(1985, 12, 31))
        enroll = _rand_date(date(2022, 1, 1), date(2022, 12, 31))
        records.append({
            "subject_id": f"{site}-{i:04d}",
            "site_id": site,
            "treatment_arm": arm,
            "sex": random.choice(SEXES),
            "race": random.choices(RACES, weights=[60, 20, 15, 5])[0],
            "ethnicity": random.choices(ETHNICITIES, weights=[20, 80])[0],
            "date_of_birth": bday.strftime("%Y-%m-%d"),
            "enrollment_date": enroll.strftime("%Y-%m-%d"),
            "consent_date": (enroll - timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
            "country": "USA",
            "completed_study": random.choices([1, 0], weights=[80, 20])[0],
        })
    return pd.DataFrame(records)


def generate_adverse_events(subjects: pd.DataFrame) -> pd.DataFrame:
    """Raw AE data — multiple AEs per subject possible."""
    ae_terms = [
        ("Nausea", "Gastrointestinal disorders", "NAUSEA"),
        ("Headache", "Nervous system disorders", "HEADACHE"),
        ("Fatigue", "General disorders", "FATIGUE"),
        ("Dizziness", "Nervous system disorders", "DIZZINESS"),
        ("Hypertension", "Vascular disorders", "HYPERTENSION"),
        ("ALT increased", "Investigations", "ALANINE AMINOTRANSFERASE INCREASED"),
        ("Rash", "Skin disorders", "RASH"),
        ("Diarrhoea", "Gastrointestinal disorders", "DIARRHOEA"),
    ]
    records = []
    seq = 1
    for _, subj in subjects.iterrows():
        n_aes = np.random.poisson(2)
        enroll = date.fromisoformat(subj["enrollment_date"])
        for _ in range(n_aes):
            term, soc, meddra = random.choice(ae_terms)
            onset = _rand_date(enroll, enroll + timedelta(days=180))
            duration = random.randint(1, 30)
            records.append({
                "ae_seq": seq,
                "subject_id": subj["subject_id"],
                "ae_term": term,
                "ae_soc": soc,
                "ae_meddra_pt": meddra,
                "ae_severity": random.choices(["MILD", "MODERATE", "SEVERE"], weights=[60, 30, 10])[0],
                "ae_serious": random.choices(["Y", "N"], weights=[10, 90])[0],
                "ae_related": random.choices(["Y", "N"], weights=[40, 60])[0],
                "ae_start_date": onset.strftime("%Y-%m-%d"),
                "ae_end_date": (onset + timedelta(days=duration)).strftime("%Y-%m-%d"),
                "ae_action_taken": random.choice(["NONE", "DOSE REDUCED", "DRUG WITHDRAWN"]),
            })
            seq += 1
    return pd.DataFrame(records)


def generate_vital_signs(subjects: pd.DataFrame) -> pd.DataFrame:
    """Raw vital signs — collected at screening, day 1, week 4, week 8, week 12."""
    visits = {
        "SCREENING": -7,
        "DAY 1": 1,
        "WEEK 4": 28,
        "WEEK 8": 56,
        "WEEK 12": 84,
    }
    records = []
    seq = 1
    for _, subj in subjects.iterrows():
        enroll = date.fromisoformat(subj["enrollment_date"])
        base_sbp = random.gauss(130, 15)
        base_dbp = random.gauss(82, 10)
        base_hr = random.gauss(72, 10)
        base_temp = random.gauss(36.6, 0.3)
        base_weight = random.gauss(80, 15)
        for visit, day_offset in visits.items():
            vdate = enroll + timedelta(days=day_offset)
            records.append({
                "vs_seq": seq,
                "subject_id": subj["subject_id"],
                "visit": visit,
                "visit_day": day_offset,
                "vs_date": vdate.strftime("%Y-%m-%d"),
                "systolic_bp": round(base_sbp + random.gauss(0, 5), 1),
                "diastolic_bp": round(base_dbp + random.gauss(0, 3), 1),
                "heart_rate": round(base_hr + random.gauss(0, 4), 1),
                "temperature": round(base_temp + random.gauss(0, 0.2), 1),
                "weight_kg": round(base_weight + random.gauss(0, 1), 1),
                "height_cm": round(random.gauss(170, 10), 1) if visit == "SCREENING" else None,
            })
            seq += 1
    return pd.DataFrame(records)


def generate_lab_results(subjects: pd.DataFrame) -> pd.DataFrame:
    """Raw laboratory results."""
    panels = [
        ("ALT", "U/L", 7, 56, 30, 10),
        ("AST", "U/L", 10, 40, 25, 8),
        ("Creatinine", "mg/dL", 0.6, 1.2, 0.9, 0.15),
        ("Haemoglobin", "g/dL", 12, 17, 14, 1.2),
        ("Platelets", "10^9/L", 150, 400, 250, 40),
        ("WBC", "10^9/L", 4, 11, 7, 1.5),
        ("Glucose", "mg/dL", 70, 110, 90, 12),
    ]
    visits = ["SCREENING", "WEEK 4", "WEEK 12"]
    records = []
    seq = 1
    for _, subj in subjects.iterrows():
        enroll = date.fromisoformat(subj["enrollment_date"])
        for visit in visits:
            day_map = {"SCREENING": -7, "WEEK 4": 28, "WEEK 12": 84}
            ldate = enroll + timedelta(days=day_map[visit])
            for test, unit, lo_n, hi_n, mean, sd in panels:
                val = round(random.gauss(mean, sd), 2)
                records.append({
                    "lb_seq": seq,
                    "subject_id": subj["subject_id"],
                    "visit": visit,
                    "lb_date": ldate.strftime("%Y-%m-%d"),
                    "lb_test": test,
                    "lb_result": val,
                    "lb_unit": unit,
                    "lb_ref_lo": lo_n,
                    "lb_ref_hi": hi_n,
                    "lb_nrind": "LOW" if val < lo_n else ("HIGH" if val > hi_n else "NORMAL"),
                })
                seq += 1
    return pd.DataFrame(records)


def generate_exposure(subjects: pd.DataFrame) -> pd.DataFrame:
    """Raw drug exposure / dosing records."""
    records = []
    seq = 1
    for _, subj in subjects.iterrows():
        enroll = date.fromisoformat(subj["enrollment_date"])
        drug = "ACTIVE DRUG 100MG" if subj["treatment_arm"] == "A" else "PLACEBO"
        n_doses = random.randint(70, 84)
        for d in range(n_doses):
            records.append({
                "ex_seq": seq,
                "subject_id": subj["subject_id"],
                "ex_trt": drug,
                "ex_dose": 100 if subj["treatment_arm"] == "A" else 0,
                "ex_dose_unit": "mg",
                "ex_route": "ORAL",
                "ex_start_date": (enroll + timedelta(days=d)).strftime("%Y-%m-%d"),
                "ex_end_date": (enroll + timedelta(days=d)).strftime("%Y-%m-%d"),
            })
            seq += 1
    return pd.DataFrame(records)


def generate_concomitant_meds(subjects: pd.DataFrame) -> pd.DataFrame:
    """Raw concomitant medications."""
    meds = [
        ("Aspirin", "ASPIRIN", "ANTITHROMBOTIC AGENTS"),
        ("Metformin", "METFORMIN", "DRUGS USED IN DIABETES"),
        ("Lisinopril", "LISINOPRIL", "AGENTS ACTING ON THE RENIN-ANGIOTENSIN SYSTEM"),
        ("Atorvastatin", "ATORVASTATIN", "LIPID MODIFYING AGENTS"),
        ("Omeprazole", "OMEPRAZOLE", "DRUGS FOR ACID RELATED DISORDERS"),
    ]
    records = []
    seq = 1
    for _, subj in subjects.iterrows():
        enroll = date.fromisoformat(subj["enrollment_date"])
        for med, generic, atc in random.sample(meds, k=random.randint(0, 3)):
            records.append({
                "cm_seq": seq,
                "subject_id": subj["subject_id"],
                "cm_term": med,
                "cm_generic": generic,
                "cm_atc_class": atc,
                "cm_start_date": _rand_date(enroll - timedelta(days=90), enroll).strftime("%Y-%m-%d"),
                "cm_end_date": _rand_date(enroll + timedelta(days=30), enroll + timedelta(days=180)).strftime("%Y-%m-%d"),
                "cm_ongoing": "N",
                "cm_indication": "CHRONIC CONDITION",
            })
            seq += 1
    return pd.DataFrame(records)


def generate_all(output_dir: str = "data/raw") -> dict[str, pd.DataFrame]:
    import os
    os.makedirs(output_dir, exist_ok=True)
    subjects = generate_subjects()
    datasets = {
        "dm_raw": subjects,
        "ae_raw": generate_adverse_events(subjects),
        "vs_raw": generate_vital_signs(subjects),
        "lb_raw": generate_lab_results(subjects),
        "ex_raw": generate_exposure(subjects),
        "cm_raw": generate_concomitant_meds(subjects),
    }
    for name, df in datasets.items():
        df.to_csv(f"{output_dir}/{name}.csv", index=False)
    print(f"[OK] Generated {sum(len(d) for d in datasets.values())} raw records across {len(datasets)} datasets")
    return datasets


if __name__ == "__main__":
    generate_all()

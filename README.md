# CDISC SDTM & ADaM Builder

> A production-style Python pipeline that maps raw clinical trial data to **CDISC SDTM** and **ADaM** standards, validates against Pinnacle 21 rules, and generates a **define.xml** for regulatory e-submission.

![CI](https://github.com/your-username/cdisc-sdtm-adam-builder/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![CDISC](https://img.shields.io/badge/CDISC-SDTM%20v3.3%20%7C%20ADaM%20v1.3-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

This project demonstrates the core technical skills required for **Statistical Programmer** and **Clinical Data Manager** roles in pharmaceutical and CRO environments:

| Skill Area | What this project covers |
|---|---|
| CDISC SDTM v3.3 | DM, AE, VS, LB, EX, CM domain mapping |
| CDISC ADaM v1.3 | ADSL (one-per-subject), ADAE (adverse events BDS), ADLB (lab BDS with CHG/PCHG) |
| Validation | Pinnacle 21-style checks: required variables, controlled terminology, date logic, sequence uniqueness |
| define.xml | Define-XML v2.0 metadata for FDA/EMA e-submission package |
| Testing | 35 pytest unit tests covering data integrity, CT compliance, BDS logic |
| CI/CD | GitHub Actions across Python 3.10–3.12 |

All data is **100% synthetic** — generated via Faker — and is HIPAA-safe.

---

## Study Design

```
Study ID : CDISCPILOT01
Design   : Phase II, randomised, double-blind, placebo-controlled
Arms     : A = Active Drug 100mg (QD oral) | B = Placebo
Subjects : 80 (4 sites, USA)
Visits   : Screening → Day 1 → Week 4 → Week 8 → Week 12
Domains  : DM AE VS LB EX CM  →  ADSL ADAE ADLB
```

---

## Project Structure

```
cdisc-sdtm-adam-builder/
├── pipeline.py                    # Main orchestrator — run this
├── requirements.txt
├── .github/
│   └── workflows/ci.yml           # GitHub Actions CI
│
├── src/
│   ├── utils/
│   │   ├── synthetic_data.py      # Raw EDC-style data generator
│   │   └── define_xml.py          # Define-XML v2.0 generator
│   ├── sdtm/
│   │   ├── dm.py                  # Demographics domain
│   │   ├── ae.py                  # Adverse Events domain
│   │   ├── vs.py                  # Vital Signs domain (vertical)
│   │   ├── lb.py                  # Laboratory Results domain
│   │   └── ex_cm.py               # Exposure + Concomitant Meds
│   ├── adam/
│   │   ├── adsl.py                # Subject-Level Analysis Dataset
│   │   ├── adae.py                # AE Analysis Dataset (TRTEMFL, AESEVN)
│   │   └── adlb.py                # Lab Analysis Dataset (BASE, CHG, PCHG, SHIFT)
│   └── validation/
│       └── checks.py              # Pinnacle 21-style validation rules
│
├── data/
│   ├── raw/                       # Generated raw CSV files (EDC-style)
│   ├── sdtm/                      # SDTM domain CSVs
│   └── adam/                      # ADaM dataset CSVs
│
├── outputs/
│   ├── define.xml                 # Regulatory submission metadata
│   └── validation_findings.csv   # Validation report
│
└── tests/
    └── test_pipeline.py           # 35 unit tests
```

---

## Quick Start

```bash
# Clone and set up
git clone https://github.com/your-username/cdisc-sdtm-adam-builder.git
cd cdisc-sdtm-adam-builder

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt

# Run full pipeline
python pipeline.py

# Run tests
pytest tests/ -v

# Deactivate when done
deactivate
```

**Expected output:**
```
[1/5] Generating synthetic raw data ...  8,640 raw records
[2/5] Mapping to SDTM domains ...        DM AE VS LB EX CM
[3/5] Building ADaM datasets ...         ADSL ADAE ADLB
[4/5] Running CDISC validation checks ... 0 errors, 0 warnings
[5/5] Generating define.xml ...
Pipeline Complete — 12,238 total rows, 9 datasets
```

---

## SDTM Domains

### DM — Demographics
Key variables: `USUBJID SUBJID SITEID AGE AGEU SEX RACE ETHNIC COUNTRY ARMCD ARM RFSTDTC BRTHDTC`

- USUBJID format: `STUDYID-SITEID-SUBJID`
- AGE computed from birth date and enrollment date
- Controlled terminology: SEX (M/F), RACE (NCI CT), COUNTRY (ISO 3166)

### AE — Adverse Events
Key variables: `AETERM AEDECOD AEBODSYS AESEV AESER AEREL AEACN AESTDTC AEENDTC AESTDY AETOXGR`

- MedDRA coding on `AEDECOD` and `AEBODSYS`
- `AESTDY` calculated relative to `RFSTDTC`
- Severity graded per CTCAE (`AETOXGR`: 1–3)

### VS — Vital Signs
Vertical (unpivoted) structure. Tests: `SYSBP DIABP PULSE TEMP WEIGHT HEIGHT`

- One row per subject × visit × test
- `VSBLFL = Y` at Screening (baseline)

### LB — Laboratory Results
Tests: `ALT AST CREAT HGB PLAT WBC GLUC` with reference ranges and `LBNRIND`

### EX — Exposure
Daily dosing records with `EXTRT EXDOSE EXDOSU EXROUTE EXDOSFRQ EXSTDTC`

### CM — Concomitant Medications
`CMTRT CMDECOD CMATC CMROUTE CMINDC CMSTDTC CMENDTC`

---

## ADaM Datasets

### ADSL — Subject-Level Analysis Dataset
One record per subject. Key additions over DM:

| Variable | Description |
|---|---|
| `TRT01P / TRT01A` | Planned / actual treatment label |
| `TRT01PN / TRT01AN` | Numeric treatment codes (1=Active, 2=Placebo) |
| `TRTSDT / TRTEDTC` | First/last dose dates (from EX) |
| `TRTDURD` | Treatment duration in days |
| `SAFFL EFFFL ITTFL PPROTFL` | Population flags |
| `AGEGR1 / AGEGR1N` | Age group (<50, 50–65, >65) |
| `BMIBL WEIGHTBL HEIGHTBL` | Baseline measurements |

### ADAE — Adverse Events Analysis Dataset
BDS structure with treatment variables joined from ADSL.

| Variable | Description |
|---|---|
| `TRTEMFL` | Treatment-emergent flag (Y if onset ≥ first dose) |
| `AESEVN` | Numeric severity (1=Mild, 2=Moderate, 3=Severe) |
| `AESERN` | Serious AE flag numeric (0/1) |
| `AERELN` | Related AE flag numeric (0/1) |

### ADLB — Laboratory Analysis Dataset
BDS structure (one row per subject × parameter × visit).

| Variable | Description |
|---|---|
| `AVAL` | Analysis value |
| `BASE` | Baseline value (Screening) |
| `CHG` | Change from baseline (AVAL − BASE) |
| `PCHG` | Percent change from baseline |
| `ANRIND` | Normal range indicator at visit |
| `BNRIND` | Normal range indicator at baseline |
| `SHIFT1` | Shift category (e.g. `NORMAL→HIGH`) |
| `ABLFL` | Baseline flag (Y at Screening) |

---

## Validation Checks

Inspired by Pinnacle 21 Community rules:

| Rule | Domain | Description | Severity |
|---|---|---|---|
| SD0001 | DM | Required variables present | ERROR |
| SD0002 | DM | USUBJID unique | ERROR |
| SD0003 | DM | SEX controlled terminology | ERROR |
| SD0004 | Any | ISO 8601 date format | ERROR |
| SD0005 | AE | AESER = Y or N | ERROR |
| SD0006 | AE | Start date ≤ end date | ERROR |
| SD0007 | Any | SEQ unique within USUBJID | ERROR |
| AD0001 | ADSL | Required ADaM variables | ERROR |
| AD0002 | ADSL | Population flags = Y or N | ERROR |
| AD0003 | ADLB | BASE not null for post-baseline | WARNING |
| AD0004 | ADAE | TRTEMFL variable present | ERROR |

---

## Regulatory Context

This pipeline follows guidance from:
- **CDISC SDTM Implementation Guide v3.3**
- **CDISC ADaM Implementation Guide v1.3**
- **FDA Study Data Technical Conformance Guide**
- **ICH E6(R3) Good Clinical Practice**
- **21 CFR Part 11** (electronic records compliance)

---

## Extending the Project

| What to add | Where |
|---|---|
| New SDTM domain (e.g. MH, EG) | `src/sdtm/` — follow the pattern in `ae.py` |
| New ADaM dataset (e.g. ADTTE survival) | `src/adam/` |
| Additional validation rules | `src/validation/checks.py` |
| TLF output (Table 14.1.1 etc.) | See **TLF Automation Engine Project** |

---

## License

MIT — free to use and adapt for learning, portfolio, and non-commercial projects.  
All data is synthetic. This project does not contain real patient data.

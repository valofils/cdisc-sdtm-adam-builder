"""
define.xml Generator
Generates a CDISC-compliant define.xml (Define-XML v2.0) metadata file
describing the SDTM and ADaM datasets for regulatory e-submission.
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd


STUDY_ID = "CDISCPILOT01"
DEFINE_VERSION = "2.0.0"

DATASET_META = {
    "DM":   ("Demographics",                       "SDTM", "Subject-level demographic information"),
    "AE":   ("Adverse Events",                     "SDTM", "Adverse events collected during the trial"),
    "VS":   ("Vital Signs",                        "SDTM", "Vital sign measurements"),
    "LB":   ("Laboratory Test Results",            "SDTM", "Laboratory findings"),
    "EX":   ("Exposure",                           "SDTM", "Drug exposure records"),
    "CM":   ("Concomitant Medications",            "SDTM", "Concomitant medication records"),
    "ADSL": ("Subject-Level Analysis Dataset",     "ADaM", "One record per subject with treatment flags"),
    "ADAE": ("Adverse Events Analysis Dataset",    "ADaM", "Analysis-ready adverse event data"),
    "ADLB": ("Laboratory Analysis Dataset",        "ADaM", "BDS structure with baseline and change"),
}

VAR_TYPES = {
    "STUDYID": ("Char", "Study Identifier"),
    "DOMAIN":  ("Char", "Domain Abbreviation"),
    "USUBJID": ("Char", "Unique Subject Identifier"),
    "SUBJID":  ("Char", "Subject Identifier in the Study"),
    "SITEID":  ("Char", "Study Site Identifier"),
    "AGE":     ("Num",  "Age"),
    "AGEU":    ("Char", "Age Units"),
    "SEX":     ("Char", "Sex"),
    "RACE":    ("Char", "Race"),
    "ETHNIC":  ("Char", "Ethnicity"),
    "COUNTRY": ("Char", "Country"),
    "ARMCD":   ("Char", "Planned Arm Code"),
    "ARM":     ("Char", "Description of Planned Arm"),
    "SAFFL":   ("Char", "Safety Population Flag"),
    "EFFFL":   ("Char", "Efficacy Population Flag"),
    "TRT01P":  ("Char", "Planned Treatment for Period 01"),
    "TRT01A":  ("Char", "Actual Treatment for Period 01"),
    "AVAL":    ("Num",  "Analysis Value"),
    "BASE":    ("Num",  "Baseline Value"),
    "CHG":     ("Num",  "Change from Baseline"),
    "PCHG":    ("Num",  "Percent Change from Baseline"),
    "PARAMCD": ("Char", "Parameter Code"),
    "PARAM":   ("Char", "Parameter"),
    "TRTEMFL": ("Char", "Treatment Emergent Analysis Flag"),
}


def _indent(elem: ET.Element, level: int = 0) -> None:
    """Add pretty-print indentation to XML tree."""
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def generate_define_xml(
    datasets: dict[str, pd.DataFrame],
    output_path: str = "outputs/define.xml"
) -> str:
    """
    Generate define.xml for the provided datasets.

    Parameters
    ----------
    datasets : dict mapping dataset name → DataFrame
    output_path : where to write the XML file

    Returns
    -------
    str — path to generated file
    """
    root = ET.Element("ODM")
    root.set("xmlns", "http://www.cdisc.org/ns/odm/v1.3")
    root.set("xmlns:def", "http://www.cdisc.org/ns/def/v2.0")
    root.set("ODMVersion", "1.3.2")
    root.set("FileOID", f"{STUDY_ID}.define")
    root.set("FileType", "Snapshot")
    root.set("CreationDateTime", datetime.utcnow().isoformat() + "Z")
    root.set("def:Context", "Other")

    study = ET.SubElement(root, "Study")
    study.set("OID", STUDY_ID)

    global_vars = ET.SubElement(study, "GlobalVariables")
    ET.SubElement(global_vars, "StudyName").text = STUDY_ID
    ET.SubElement(global_vars, "StudyDescription").text = "CDISC Pilot Study 01 — Synthetic Dataset"
    ET.SubElement(global_vars, "ProtocolName").text = STUDY_ID

    meta_data = ET.SubElement(study, "MetaDataVersion")
    meta_data.set("OID", f"{STUDY_ID}.MDV.001")
    meta_data.set("Name", "Define-XML v2.0")
    meta_data.set("def:DefineVersion", DEFINE_VERSION)

    # Dataset definitions
    for ds_name, df in datasets.items():
        if ds_name not in DATASET_META:
            continue
        label, cls, desc = DATASET_META[ds_name]

        item_group = ET.SubElement(meta_data, "ItemGroupDef")
        item_group.set("OID", f"IG.{ds_name}")
        item_group.set("Name", ds_name)
        item_group.set("Repeating", "Yes" if ds_name != "ADSL" else "No")
        item_group.set("IsReferenceData", "No")
        item_group.set("SASDatasetName", ds_name)
        item_group.set("def:Label", label)
        item_group.set("def:Class", cls)
        item_group.set("def:Structure", desc)

        desc_elem = ET.SubElement(item_group, "Description")
        ET.SubElement(desc_elem, "TranslatedText").text = desc

        # Add variable refs
        for col in df.columns:
            ref = ET.SubElement(item_group, "ItemRef")
            ref.set("ItemOID", f"IT.{ds_name}.{col}")
            ref.set("Mandatory", "Yes" if col in ("STUDYID", "DOMAIN", "USUBJID") else "No")

        # ItemDef per variable
        for col in df.columns:
            dtype, col_label = VAR_TYPES.get(col, ("Char", col))
            item_def = ET.SubElement(meta_data, "ItemDef")
            item_def.set("OID", f"IT.{ds_name}.{col}")
            item_def.set("Name", col)
            item_def.set("DataType", "text" if dtype == "Char" else "float")
            item_def.set("Length", "200" if dtype == "Char" else "8")
            item_def.set("SASFieldName", col[:8])
            item_def.set("def:Label", col_label)
            desc2 = ET.SubElement(item_def, "Description")
            ET.SubElement(desc2, "TranslatedText").text = col_label

    _indent(root)
    tree = ET.ElementTree(root)

    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)

    print(f"[OK] define.xml written to {output_path}")
    return output_path

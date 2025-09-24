import io
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd


CASE_COLUMNS = [
    "Case ID",
    "Seller ID",
    "Seller Name",
    "Specialist ID",
    "Specialist Name",
    "Marketplace",
    "Case Source",
    "Case Status",
    "Workstream",
    "Listing Start Date",
    "Listing Completion Date",
    "Issue Type",
    "Complexity",
    "Priority",
    "API Supported",
    "Integration Type",
    "Seller Type",
    "Feedback Received",
    "CSAT Score",
    "Notes",
    "Last Sub-Status",
]

UPDATE_COLUMNS = [
    "ID",
    "Case ID",
    "Note",
    "Updated By",
    "Timestamp",
    "Sub Status",
]


def build_export_workbook(
    cases: List[Dict], updates: List[Dict]
) -> bytes:
    buffer = io.BytesIO()

    cases_df = pd.DataFrame(
        [
            {
                "Case ID": c["case_id"],
                "Seller ID": c["seller_id"],
                "Seller Name": c["seller_name"],
                "Specialist ID": c["specialist_id"],
                "Specialist Name": c["specialist_name"],
                "Marketplace": c["marketplace"],
                "Case Source": c["case_source"],
                "Case Status": c["case_status"],
                "Workstream": c["workstream"],
                "Listing Start Date": c.get("listing_start_date") or "",
                "Listing Completion Date": c.get("listing_completion_date") or "",
                "Issue Type": ", ".join(c.get("issue_type", [])),
                "Complexity": c["complexity"],
                "Priority": c["priority"],
                "API Supported": ", ".join(c.get("api_supported", [])),
                "Integration Type": c["integration_type"],
                "Seller Type": c["seller_type"],
                "Feedback Received": "Yes" if c.get("feedback_received") else "No",
                "CSAT Score": c.get("csat_score") or "",
                "Notes": c.get("notes") or "",
                "Last Sub-Status": c.get("last_sub_status") or "",
            }
            for c in cases
        ]
    )

    updates_df = pd.DataFrame(
        [
            {
                "ID": u["id"],
                "Case ID": u["case_id"],
                "Note": u["note"],
                "Updated By": u["updated_by"],
                "Timestamp": u["timestamp"],
                "Sub Status": u["sub_status"],
            }
            for u in updates
        ]
    )

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        cases_df.to_excel(writer, index=False, sheet_name="Cases")
        updates_df.to_excel(writer, index=False, sheet_name="Updates")

    buffer.seek(0)
    return buffer.getvalue()


def build_empty_template() -> bytes:
    buffer = io.BytesIO()
    empty_cases = pd.DataFrame(columns=CASE_COLUMNS)
    empty_updates = pd.DataFrame(columns=UPDATE_COLUMNS)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        empty_cases.to_excel(writer, index=False, sheet_name="Cases")
        empty_updates.to_excel(writer, index=False, sheet_name="Updates")

    buffer.seek(0)
    return buffer.getvalue()


def parse_import_workbook(file) -> Tuple[List[Dict], List[Dict]]:
    xl = pd.ExcelFile(file)
    if "Cases" not in xl.sheet_names or "Updates" not in xl.sheet_names:
        raise ValueError('Workbook must contain "Cases" and "Updates" sheets.')

    cases_df = xl.parse("Cases")
    updates_df = xl.parse("Updates")

    cases: List[Dict] = []
    for _, row in cases_df.iterrows():
        case_id = str(row.get("Case ID", "")).strip()
        if not case_id:
            raise ValueError("Each case row must include a Case ID.")

        issue_type = [
            part.strip()
            for part in str(row.get("Issue Type", "")).split(",")
            if part.strip()
        ]
        api_supported = [
            part.strip()
            for part in str(row.get("API Supported", "")).split(",")
            if part.strip()
        ]

        cases.append(
            {
                "case_id": case_id,
                "seller_id": int(row.get("Seller ID", 0) or 0),
                "seller_name": str(row.get("Seller Name", "")).strip(),
                "specialist_id": str(row.get("Specialist ID", "")).strip(),
                "specialist_name": str(row.get("Specialist Name", "")).strip(),
                "marketplace": str(row.get("Marketplace", "")).strip(),
                "case_source": str(row.get("Case Source", "")).strip(),
                "case_status": str(row.get("Case Status", "")).strip(),
                "workstream": str(row.get("Workstream", "")).strip(),
                "listing_start_date": _to_iso_date(row.get("Listing Start Date")),
                "listing_completion_date": _to_iso_date(
                    row.get("Listing Completion Date")
                ),
                "issue_type": issue_type,
                "complexity": str(row.get("Complexity", "")).strip(),
                "priority": str(row.get("Priority", "")).strip(),
                "api_supported": api_supported,
                "integration_type": str(row.get("Integration Type", "")).strip(),
                "seller_type": str(row.get("Seller Type", "")).strip(),
                "feedback_received": str(row.get("Feedback Received", "")).strip()
                .lower()
                .startswith("y"),
                "csat_score": _to_float(row.get("CSAT Score")),
                "notes": str(row.get("Notes", "")).strip(),
                "last_sub_status": str(row.get("Last Sub-Status", "")).strip() or None,
            }
        )

    updates: List[Dict] = []
    for _, row in updates_df.iterrows():
        case_id = str(row.get("Case ID", "")).strip()
        if not case_id:
            continue
        timestamp_raw = row.get("Timestamp")
        timestamp = _to_iso_datetime(timestamp_raw)
        updates.append(
            {
                "id": int(row["ID"]) if not pd.isna(row.get("ID")) else None,
                "case_id": case_id,
                "note": str(row.get("Note", "")).strip(),
                "updated_by": str(row.get("Updated By", "")).strip(),
                "timestamp": timestamp,
                "sub_status": str(row.get("Sub Status", "")).strip(),
            }
        )

    return cases, updates


def _to_iso_date(value) -> str:
    if pd.isna(value) or value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return ""
        try:
            return pd.to_datetime(value).date().isoformat()
        except Exception:
            return value
    if isinstance(value, (int, float)):
        ts = pd.to_datetime(value, unit="d", origin="1899-12-30")
        return ts.date().isoformat()
    return str(value)


def _to_iso_datetime(value) -> str:
    if pd.isna(value) or value is None or value == "":
        return datetime.utcnow().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        return pd.to_datetime(value).to_pydatetime().isoformat()
    except Exception:
        return datetime.utcnow().isoformat()


def _to_float(value) -> float:
    if pd.isna(value) or value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from typing import Dict, List, Optional

import db
import excel_utils

MARKETPLACES = ["EU5", "EU", "3PX", "MENA", "AU", "SG", "NA", "JP", "ZA"]
CASE_SOURCES = ["ASTRO", "WINSTON"]
CASE_STATUSES = [
    "SUBMITTED",
    "AWAITING INFORMATION",
    "CANCELLED",
    "ON-HOLD",
    "WIP",
    "COMPLETED",
]
WORKSTREAMS = [
    "PAID",
    "STRATEGIC_PRODUCT_SMART_CONNECT_EU",
    "DSR",
    "STRATEGIC_PRODUCT_SMART_CONNECT_MENA",
    "STRATEGIC_DEVELOPER_LUXURY_NA",
    "MIGRATION_M@UMP",
    "STRATEGIC_DSR",
    "STRATEGIC_DEVELOPER_LUXURY_EU",
    "F3",
    "LUXURY STORE",
    "STRATEGIC_PRODUCT_SMART_CONNECT_AU",
    "B2B",
    "STRATEGIC_PRODUCT_MFG",
    "BRAND_AGENCY",
    "DSR_3PD",
    "STRATEGIC_PRODUCT_SMART_CONNECT_AES_AU",
]
COMPLEXITIES = ["Easy", "Medium", "Hard"]
PRIORITIES = ["Low", "Medium", "High"]
SELLER_TYPES = ["NEW", "EXISTING"]
SUB_STATUSES = [
    "INT_START",
    "INT_WIP",
    "ON_HOLD",
    "PMA_DRAF",
    "MAC",
    "PAA_DRAF",
    "AAC",
    "PMA",
    "PAA",
    "ASSIGNED",
    "KO_SENT",
    "PMA_FUP_1",
    "PMA_FUP_2",
    "PMA_FUP_3",
    "PAC",
    "CANCELLED",
    "Case_Created",
    "PMCA",
    "Note",
    "PMA_FUP_4",
    "SUPPORT",
    "HANDOVER",
]


def init_state():
    st.session_state.setdefault("case_filters", {})
    st.session_state.setdefault("selected_case_id", None)
    st.session_state.setdefault("edit_case_id", None)
    st.session_state.setdefault("edit_update_id", None)
    st.session_state.setdefault("updates_case_filter", "All")
    st.session_state.setdefault("show_case_form", False)
    st.session_state.setdefault("show_update_form", False)
    st.session_state.setdefault("selected_update_case", None)


def main():
    st.set_page_config(
        page_title="Case Management System",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    db.init_db()
    init_state()

    st.title("Case Management System (Streamlit)")

    tab_cases, tab_updates = st.tabs(["Cases", "Updates"])

    with tab_cases:
        render_cases_tab()

    with tab_updates:
        render_updates_tab()


def render_cases_tab():
    st.subheader("Case Management")

    metrics = db.fetch_summary_counts()
    cols = st.columns(5)
    cols[0].metric("Total Cases", metrics["total"])
    cols[1].metric("Submitted", metrics["SUBMITTED"])
    cols[2].metric("WIP", metrics["WIP"])
    cols[3].metric("Completed", metrics["COMPLETED"])
    cols[4].metric("Cancelled", metrics["CANCELLED"])

    render_option_manager()

    st.markdown("#### Filters")
    with st.form(key="case_filters_form"):
        filter_cols = st.columns(4)
        st.session_state.case_filters["case_id"] = filter_cols[0].text_input(
            "Case ID contains",
            value=st.session_state.case_filters.get("case_id", ""),
        )
        st.session_state.case_filters["case_status"] = filter_cols[1].text_input(
            "Status contains",
            value=st.session_state.case_filters.get("case_status", ""),
        )
        st.session_state.case_filters["seller_name"] = filter_cols[2].text_input(
            "Seller contains",
            value=st.session_state.case_filters.get("seller_name", ""),
        )
        st.session_state.case_filters["specialist_name"] = filter_cols[3].text_input(
            "Specialist contains",
            value=st.session_state.case_filters.get("specialist_name", ""),
        )

        filter_cols2 = st.columns(4)
        st.session_state.case_filters["marketplace"] = filter_cols2[0].text_input(
            "Marketplace contains",
            value=st.session_state.case_filters.get("marketplace", ""),
        )
        st.session_state.case_filters["workstream"] = filter_cols2[1].text_input(
            "Workstream contains",
            value=st.session_state.case_filters.get("workstream", ""),
        )
        st.session_state.case_filters["priority"] = filter_cols2[2].text_input(
            "Priority contains",
            value=st.session_state.case_filters.get("priority", ""),
        )
        st.session_state.case_filters["issue_type"] = filter_cols2[3].text_input(
            "Issue Type contains",
            value=st.session_state.case_filters.get("issue_type", ""),
        )

        submitted = st.form_submit_button("Apply filters")
        if submitted:
            st.success("Filters applied. Scroll down to view results.")

    cases = db.list_cases(st.session_state.case_filters)

    buttons_col, _, download_col = st.columns([2, 4, 3])
    if buttons_col.button("➕ Add new case", use_container_width=True):
        st.session_state.edit_case_id = None
        st.session_state.show_case_form = True

    export_bytes = excel_utils.build_export_workbook(
        cases, db.list_updates()
    )
    download_col.download_button(
        "⬇️ Export to Excel",
        data=export_bytes,
        file_name="CaseManagement_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    template_bytes = excel_utils.build_empty_template()
    download_col.download_button(
        "📄 Download Excel Template",
        data=template_bytes,
        file_name="CaseManagement_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="download_template",
    )

    st.markdown("#### Import from Excel")
    importer_cols = st.columns([2, 1])
    uploaded_file = importer_cols[0].file_uploader(
        "Upload Excel file", type=["xlsx", "xls"], key="cases_import"
    )
    if uploaded_file and importer_cols[1].button("Import", use_container_width=True):
        import_cases_from_excel(uploaded_file)
        st.rerun()

    st.markdown("#### Cases Table")
    if cases:
        cases_df = pd.DataFrame(cases)
        display_df = cases_df.copy()
        display_df["issue_type"] = display_df["issue_type"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )
        display_df["api_supported"] = display_df["api_supported"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        case_ids = [case["case_id"] for case in cases]

        st.markdown("#### Case Actions")
        st.session_state.selected_case_id = st.selectbox(
            "Select a case",
            options=[""] + case_ids,
            index=(
                case_ids.index(st.session_state.selected_case_id) + 1
                if st.session_state.selected_case_id in case_ids
                else 0
            ),
        )

        if st.session_state.selected_case_id:
            selected_case = db.get_case(st.session_state.selected_case_id)
            if selected_case:
                render_case_details(selected_case)
    else:
        st.info("No cases found. Use 'Add new case' to create one.")

    if st.session_state.show_case_form:
        case_to_edit = (
            db.get_case(st.session_state.edit_case_id)
            if st.session_state.edit_case_id
            else None
        )
        render_case_form(case_to_edit)


def render_option_manager():
    with st.expander("Manage dropdown options"):
        api_col, issue_col = st.columns(2)
        with api_col:
            st.markdown("**API options**")
            st.write(", ".join(db.list_api_options()) or "—")
            new_api = st.text_input("Add API option", key="new_api_option")
            if st.button("Save API option"):
                if new_api.strip():
                    db.add_api_option(new_api.strip())
                    st.success(f"Added API option: {new_api.strip()}")
                    st.rerun()
                else:
                    st.warning("Provide a non-empty value.")

        with issue_col:
            st.markdown("**Issue options**")
            st.write(", ".join(db.list_issue_options()) or "—")
            new_issue = st.text_input("Add issue type", key="new_issue_option")
            if st.button("Save issue type"):
                if new_issue.strip():
                    db.add_issue_option(new_issue.strip())
                    st.success(f"Added issue type: {new_issue.strip()}")
                    st.rerun()
                else:
                    st.warning("Provide a non-empty value.")


def render_case_details(case: Dict):
    st.markdown("##### Selected Case Details")
    info_cols = st.columns(4)
    info_cols[0].metric("Case ID", case["case_id"])
    info_cols[1].metric("Status", case["case_status"])
    info_cols[2].metric("Marketplace", case["marketplace"])
    info_cols[3].metric("Priority", case["priority"])

    with st.expander("Full details", expanded=True):
        details_table = pd.DataFrame(
            {
                "Field": [
                    "Seller ID",
                    "Seller Name",
                    "Specialist ID",
                    "Specialist Name",
                    "Case Source",
                    "Workstream",
                    "Listing Start Date",
                    "Listing Completion Date",
                    "Issue Type",
                    "Complexity",
                    "API Supported",
                    "Integration Type",
                    "Seller Type",
                    "Feedback Received",
                    "CSAT Score",
                    "Notes",
                    "Last Sub-Status",
                ],
                "Value": [
                    case["seller_id"],
                    case["seller_name"],
                    case["specialist_id"],
                    case["specialist_name"],
                    case["case_source"],
                    case["workstream"],
                    case.get("listing_start_date") or "—",
                    case.get("listing_completion_date") or "—",
                    ", ".join(case.get("issue_type", [])) or "—",
                    case["complexity"],
                    ", ".join(case.get("api_supported", [])) or "—",
                    case["integration_type"],
                    case["seller_type"],
                    "Yes" if case.get("feedback_received") else "No",
                    case.get("csat_score") if case.get("csat_score") is not None else "—",
                    case.get("notes") or "—",
                    case.get("last_sub_status") or "—",
                ],
            }
        )
        st.table(details_table)

    button_cols = st.columns(3)
    if button_cols[0].button("Edit case", use_container_width=True):
        st.session_state.edit_case_id = case["case_id"]
        st.session_state.show_case_form = True

    if button_cols[1].button("Manage updates", use_container_width=True):
        st.session_state.updates_case_filter = case["case_id"]
        st.session_state.selected_update_case = case["case_id"]
        st.experimental_set_query_params(tab="Updates")

    if button_cols[2].button("Delete case", use_container_width=True):
        db.delete_case(case["case_id"])
        st.success(f"Deleted case {case['case_id']}")
        st.session_state.selected_case_id = None
        st.rerun()


def render_case_form(case: Optional[Dict]):
    st.markdown("#### Case Form")
    api_options = db.list_api_options()
    issue_options = db.list_issue_options()

    form_key = "edit_case_form" if case else "add_case_form"
    with st.form(key=form_key):
        case_id = st.text_input(
            "Case ID",
            value=case["case_id"] if case else "",
            disabled=bool(case),
        )
        seller_id = st.number_input(
            "Seller ID", value=int(case["seller_id"]) if case else 0, min_value=0
        )
        seller_name = st.text_input(
            "Seller Name", value=case["seller_name"] if case else ""
        )
        specialist_id = st.text_input(
            "Specialist ID", value=case["specialist_id"] if case else ""
        )
        specialist_name = st.text_input(
            "Specialist Name", value=case["specialist_name"] if case else ""
        )
        marketplace = st.selectbox(
            "Marketplace",
            options=MARKETPLACES,
            index=MARKETPLACES.index(case["marketplace"])
            if case and case["marketplace"] in MARKETPLACES
            else 0,
        )
        case_source = st.selectbox(
            "Case Source",
            options=CASE_SOURCES,
            index=CASE_SOURCES.index(case["case_source"])
            if case and case["case_source"] in CASE_SOURCES
            else 0,
        )
        case_status = st.selectbox(
            "Case Status",
            options=CASE_STATUSES,
            index=CASE_STATUSES.index(case["case_status"])
            if case and case["case_status"] in CASE_STATUSES
            else 0,
        )
        workstream = st.selectbox(
            "Workstream",
            options=WORKSTREAMS,
            index=WORKSTREAMS.index(case["workstream"])
            if case and case["workstream"] in WORKSTREAMS
            else 0,
        )

        listing_start_date = st.date_input(
            "Listing Start Date",
            value=_to_date(case.get("listing_start_date")) if case else date.today(),
        )
        listing_completion_date = st.date_input(
            "Listing Completion Date",
            value=_to_date(case.get("listing_completion_date"))
            if case and case.get("listing_completion_date")
            else date.today(),
        )
        issue_type = st.multiselect(
            "Issue Type",
            options=issue_options,
            default=case["issue_type"] if case else [],
        )
        complexity = st.selectbox(
            "Complexity",
            options=COMPLEXITIES,
            index=COMPLEXITIES.index(case["complexity"])
            if case and case["complexity"] in COMPLEXITIES
            else 0,
        )
        priority = st.selectbox(
            "Priority",
            options=PRIORITIES,
            index=PRIORITIES.index(case["priority"])
            if case and case["priority"] in PRIORITIES
            else 0,
        )
        api_supported = st.multiselect(
            "Supported APIs",
            options=api_options,
            default=case["api_supported"] if case else [],
        )
        integration_type = st.text_input(
            "Integration Type", value=case["integration_type"] if case else ""
        )
        seller_type = st.selectbox(
            "Seller Type",
            options=SELLER_TYPES,
            index=SELLER_TYPES.index(case["seller_type"])
            if case and case["seller_type"] in SELLER_TYPES
            else 0,
        )
        feedback_received = st.checkbox(
            "Feedback received?",
            value=case["feedback_received"] if case else False,
        )
        csat_score = st.number_input(
            "CSAT Score",
            min_value=0.0,
            max_value=5.0,
            step=0.1,
            value=float(case["csat_score"])
            if case and case.get("csat_score") is not None
            else 0.0,
        )
        notes = st.text_area("Notes", value=case["notes"] if case else "")
        last_sub_status = st.text_input(
            "Last Sub-Status",
            value=case.get("last_sub_status") if case else "",
            help="Usually set automatically from the most recent update.",
        )

        submitted = st.form_submit_button("Save case")

        if submitted:
            payload = {
                "case_id": case["case_id"] if case else case_id.strip(),
                "seller_id": int(seller_id),
                "seller_name": seller_name.strip(),
                "specialist_id": specialist_id.strip(),
                "specialist_name": specialist_name.strip(),
                "marketplace": marketplace,
                "case_source": case_source,
                "case_status": case_status,
                "workstream": workstream,
                "listing_start_date": listing_start_date.isoformat()
                if listing_start_date
                else "",
                "listing_completion_date": listing_completion_date.isoformat()
                if listing_completion_date
                else "",
                "issue_type": issue_type,
                "complexity": complexity,
                "priority": priority,
                "api_supported": api_supported,
                "integration_type": integration_type.strip(),
                "seller_type": seller_type,
                "feedback_received": feedback_received,
                "csat_score": float(csat_score) if csat_score else None,
                "notes": notes.strip(),
                "last_sub_status": last_sub_status.strip() or None,
            }

            try:
                if case:
                    db.update_case(case["case_id"], payload)
                    st.success(f"Updated case {case['case_id']}")
                else:
                    if not payload["case_id"]:
                        st.error("Case ID is required.")
                        return
                    db.create_case(payload)
                    st.success(f"Created case {payload['case_id']}")
            except Exception as exc:
                st.error(f"Unable to save case: {exc}")
            finally:
                st.session_state.show_case_form = False
                st.rerun()


def render_updates_tab():
    st.subheader("Updates")

    cases = db.list_cases()
    case_ids = ["All"] + [case["case_id"] for case in cases]

    if st.session_state.updates_case_filter != "All":
        try:
            default_index = case_ids.index(st.session_state.updates_case_filter)
        except ValueError:
            default_index = 0
    else:
        default_index = 0

    st.session_state.updates_case_filter = st.selectbox(
        "Filter by case",
        options=case_ids,
        index=default_index,
    )

    current_case_id = (
        None
        if st.session_state.updates_case_filter == "All"
        else st.session_state.updates_case_filter
    )
    updates = db.list_updates(current_case_id)

    if updates:
        updates_df = pd.DataFrame(updates)
        st.dataframe(updates_df, use_container_width=True, hide_index=True)
    else:
        st.info("No updates found for the selected filter.")

    updates_cols = st.columns(3)
    if updates_cols[0].button("Add new update", use_container_width=True):
        st.session_state.show_update_form = True
        st.session_state.edit_update_id = None
        st.session_state.selected_update_case = current_case_id

    if st.session_state.show_update_form:
        update_to_edit = None
        if st.session_state.edit_update_id:
            update_to_edit = next(
                (
                    upd
                    for upd in updates
                    if upd["id"] == st.session_state.edit_update_id
                ),
                None,
            )
        render_update_form(update_to_edit, st.session_state.selected_update_case)

    st.markdown("#### Update Actions")
    if updates:
        ids = [u["id"] for u in updates]
        selected_update_id = st.selectbox(
            "Select update",
            options=[""] + ids,
        )
        if selected_update_id:
            selected = next(
                (u for u in updates if u["id"] == selected_update_id), None
            )
            if selected:
                st.json(selected, expanded=False)
                action_cols = st.columns(2)
                if action_cols[0].button("Edit update", use_container_width=True):
                    st.session_state.edit_update_id = selected_update_id
                    st.session_state.show_update_form = True
                    st.session_state.selected_update_case = selected["case_id"]
                if action_cols[1].button(
                    "Delete update", use_container_width=True
                ):
                    db.delete_update(selected_update_id)
                    st.success(f"Deleted update {selected_update_id}")
                    st.rerun()


def render_update_form(
    update: Optional[Dict], preselected_case: Optional[str]
):
    st.markdown("#### Update Form")

    cases = db.list_cases()
    case_ids = [case["case_id"] for case in cases]

    with st.form(key="update_form"):
        case_id = st.selectbox(
            "Case ID",
            options=case_ids,
            index=case_ids.index(update["case_id"])
            if update and update["case_id"] in case_ids
            else (
                case_ids.index(preselected_case)
                if preselected_case in case_ids
                else 0
            ),
        )
        note = st.text_area("Note", value=update["note"] if update else "")
        updated_by = st.text_input(
            "Updated by", value=update["updated_by"] if update else ""
        )

        if update:
            ts = pd.to_datetime(update["timestamp"])
            default_date = ts.date()
            default_time = ts.time()
        else:
            default_date = date.today()
            default_time = datetime.now().time()

        dt_col1, dt_col2 = st.columns(2)
        timestamp_date = dt_col1.date_input(
            "Date", value=default_date, key="update_date"
        )
        timestamp_time = dt_col2.time_input(
            "Time", value=default_time, key="update_time"
        )
        sub_status = st.selectbox(
            "Sub-status",
            options=SUB_STATUSES,
            index=SUB_STATUSES.index(update["sub_status"])
            if update and update["sub_status"] in SUB_STATUSES
            else 0,
        )

        submitted = st.form_submit_button("Save update")
        if submitted:
            timestamp = datetime.combine(timestamp_date, timestamp_time).isoformat()
            payload = {
                "case_id": case_id,
                "note": note.strip(),
                "updated_by": updated_by.strip(),
                "timestamp": timestamp,
                "sub_status": sub_status,
            }
            try:
                if update:
                    db.update_update(update["id"], payload)
                    st.success(f"Updated update #{update['id']}")
                else:
                    new_id = db.create_update(payload)
                    st.success(f"Created update #{new_id}")
            except Exception as exc:
                st.error(f"Unable to save update: {exc}")
            finally:
                st.session_state.show_update_form = False
                st.session_state.edit_update_id = None
                st.rerun()


def import_cases_from_excel(file):
    try:
        cases, updates = excel_utils.parse_import_workbook(file)
    except Exception as exc:
        st.error(f"Import failed: {exc}")
        return

    created_cases = 0
    skipped_cases = 0
    created_updates = 0
    skipped_updates = 0

    for case in cases:
        existing = db.get_case(case["case_id"])
        if existing:
            skipped_cases += 1
            continue
        db.create_case(case)
        created_cases += 1

    for update in updates:
        if update["case_id"] and db.get_case(update["case_id"]):
            try:
                db.create_update(update)
                created_updates += 1
            except Exception:
                skipped_updates += 1
        else:
            skipped_updates += 1

    st.success(
        f"Import complete — cases: {created_cases} created, {skipped_cases} skipped; "
        f"updates: {created_updates} created, {skipped_updates} skipped."
    )


def _to_date(value: Optional[str]) -> date:
    if not value:
        return date.today()
    return pd.to_datetime(value).date()


if __name__ == "__main__":
    main()
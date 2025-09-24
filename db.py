import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = Path("case_mgmt.db")

DEFAULT_API_OPTIONS = [
    "REST API",
    "GraphQL",
    "Webhook",
    "SOAP",
]

DEFAULT_ISSUE_OPTIONS = [
    "API Issue",
    "Integration Problem",
    "Data Sync",
    "Configuration Error",
    "Bug",
    "Enhancement",
    "Other",
]


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;

            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                seller_id INTEGER NOT NULL,
                seller_name TEXT NOT NULL,
                specialist_id TEXT NOT NULL,
                specialist_name TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                case_source TEXT NOT NULL,
                case_status TEXT NOT NULL,
                workstream TEXT NOT NULL,
                listing_start_date TEXT,
                listing_completion_date TEXT,
                issue_type TEXT NOT NULL,
                complexity TEXT NOT NULL,
                priority TEXT NOT NULL,
                api_supported TEXT NOT NULL,
                integration_type TEXT NOT NULL,
                seller_type TEXT NOT NULL,
                feedback_received INTEGER NOT NULL,
                csat_score REAL,
                notes TEXT,
                last_sub_status TEXT
            );

            CREATE TABLE IF NOT EXISTS updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                note TEXT NOT NULL,
                updated_by TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sub_status TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS api_options (
                name TEXT PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS issue_options (
                name TEXT PRIMARY KEY
            );
            """
        )

    seed_option_table("api_options", DEFAULT_API_OPTIONS)
    seed_option_table("issue_options", DEFAULT_ISSUE_OPTIONS)


def seed_option_table(table: str, values: List[str]) -> None:
    with get_connection() as conn:
        conn.executemany(
            f"INSERT OR IGNORE INTO {table}(name) VALUES (?)",
            [(value,) for value in values],
        )


def serialize_list(value: List[str]) -> str:
    return json.dumps(value)


def deserialize_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return [item.strip() for item in value.split(",") if item.strip()]


def normalize_case_row(row: sqlite3.Row) -> Dict[str, Any]:
    record = dict(row)
    record["issue_type"] = deserialize_list(record.get("issue_type"))
    record["api_supported"] = deserialize_list(record.get("api_supported"))
    record["feedback_received"] = bool(record.get("feedback_received"))
    return record


def list_cases(filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    filters = filters or {}
    clauses: List[str] = []
    params: Dict[str, Any] = {}

    text_columns = {
        "case_id",
        "case_status",
        "last_sub_status",
        "seller_name",
        "specialist_name",
        "marketplace",
        "workstream",
        "priority",
        "issue_type",
    }

    for key, value in filters.items():
        if not value or key not in text_columns:
            continue
        clauses.append(f"LOWER({key}) LIKE :{key}")
        params[key] = f"%{value.lower()}%"

    query = "SELECT * FROM cases"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY case_id COLLATE NOCASE"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [normalize_case_row(row) for row in rows]


def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()

    if not row:
        return None
    return normalize_case_row(row)


def create_case(case_data: Dict[str, Any]) -> None:
    payload = case_data.copy()
    payload["issue_type"] = serialize_list(case_data.get("issue_type", []))
    payload["api_supported"] = serialize_list(case_data.get("api_supported", []))
    payload["feedback_received"] = 1 if case_data.get("feedback_received") else 0

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO cases (
                case_id, seller_id, seller_name, specialist_id, specialist_name,
                marketplace, case_source, case_status, workstream,
                listing_start_date, listing_completion_date, issue_type, complexity,
                priority, api_supported, integration_type, seller_type,
                feedback_received, csat_score, notes, last_sub_status
            )
            VALUES (
                :case_id, :seller_id, :seller_name, :specialist_id, :specialist_name,
                :marketplace, :case_source, :case_status, :workstream,
                :listing_start_date, :listing_completion_date, :issue_type, :complexity,
                :priority, :api_supported, :integration_type, :seller_type,
                :feedback_received, :csat_score, :notes, :last_sub_status
            )
            """,
            payload,
        )


def update_case(case_id: str, case_data: Dict[str, Any]) -> None:
    payload = case_data.copy()
    payload["issue_type"] = serialize_list(case_data.get("issue_type", []))
    payload["api_supported"] = serialize_list(case_data.get("api_supported", []))
    payload["feedback_received"] = 1 if case_data.get("feedback_received") else 0
    payload["case_id"] = case_id

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE cases
            SET
                seller_id = :seller_id,
                seller_name = :seller_name,
                specialist_id = :specialist_id,
                specialist_name = :specialist_name,
                marketplace = :marketplace,
                case_source = :case_source,
                case_status = :case_status,
                workstream = :workstream,
                listing_start_date = :listing_start_date,
                listing_completion_date = :listing_completion_date,
                issue_type = :issue_type,
                complexity = :complexity,
                priority = :priority,
                api_supported = :api_supported,
                integration_type = :integration_type,
                seller_type = :seller_type,
                feedback_received = :feedback_received,
                csat_score = :csat_score,
                notes = :notes,
                last_sub_status = :last_sub_status
            WHERE case_id = :case_id
            """,
            payload,
        )


def delete_case(case_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))


def list_updates(case_id: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "SELECT * FROM updates"
    params: Tuple[Any, ...] = ()
    if case_id:
        query += " WHERE case_id = ?"
        params = (case_id,)
    query += " ORDER BY datetime(timestamp) DESC, id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def create_update(update_data: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO updates (case_id, note, updated_by, timestamp, sub_status)
            VALUES (:case_id, :note, :updated_by, :timestamp, :sub_status)
            """,
            update_data,
        )
        update_case_last_sub_status(conn, update_data["case_id"])
        return cursor.lastrowid


def update_update(update_id: int, update_data: Dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE updates
            SET
                case_id = :case_id,
                note = :note,
                updated_by = :updated_by,
                timestamp = :timestamp,
                sub_status = :sub_status
            WHERE id = :id
            """,
            {**update_data, "id": update_id},
        )
        update_case_last_sub_status(conn, update_data["case_id"])


def delete_update(update_id: int) -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT case_id FROM updates WHERE id = ?", (update_id,)
        ).fetchone()
        if not row:
            return
        case_id = row["case_id"]
        conn.execute("DELETE FROM updates WHERE id = ?", (update_id,))
        update_case_last_sub_status(conn, case_id)


def update_case_last_sub_status(conn: sqlite3.Connection, case_id: str) -> None:
    latest = conn.execute(
        """
        SELECT sub_status
        FROM updates
        WHERE case_id = ?
        ORDER BY datetime(timestamp) DESC, id DESC
        LIMIT 1
        """,
        (case_id,),
    ).fetchone()

    new_status = latest["sub_status"] if latest else None
    conn.execute(
        "UPDATE cases SET last_sub_status = ? WHERE case_id = ?",
        (new_status, case_id),
    )


def fetch_summary_counts() -> Dict[str, int]:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        statuses = conn.execute(
            """
            SELECT case_status, COUNT(*) as cnt
            FROM cases
            GROUP BY case_status
            """
        ).fetchall()

    counts = {
        "total": total,
        "SUBMITTED": 0,
        "AWAITING INFORMATION": 0,
        "CANCELLED": 0,
        "ON-HOLD": 0,
        "WIP": 0,
        "COMPLETED": 0,
    }
    for row in statuses:
        counts[row["case_status"]] = row["cnt"]
    return counts


def list_api_options() -> List[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM api_options ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [row["name"] for row in rows]


def list_issue_options() -> List[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM issue_options ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [row["name"] for row in rows]


def add_api_option(name: str) -> None:
    if not name:
        return
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO api_options(name) VALUES (?)", (name,))


def add_issue_option(name: str) -> None:
    if not name:
        return
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO issue_options(name) VALUES (?)", (name,)
        )
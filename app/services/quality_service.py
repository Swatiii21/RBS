"""Total Quality Management (TQM) Quality Analytics Service.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Implements core TQM methods:
1. Defect Log and Checksheet: Tracking defects through the lifecycle
   (Reported -> Investigating -> Fix Implemented -> Verified -> Closed).
2. Pareto Analysis (80/20 Rule): Categorization, frequency sorting, cumulative
   percentages, and empirical evaluation of vital few vs. trivial many.
3. Ishikawa / Fishbone Analysis: Root-cause taxonomy across 6 dimensions
   (People, Process, Software Code, Database, Testing, Infrastructure).
4. Failure Mode and Effects Analysis (FMEA): Risk Priority Number (RPN) computation
   (RPN = Severity * Occurrence * Detection) on a 1-10 rating scale.
5. Continuous Improvement Tracker (PDCA): Structured Plan-Do-Check-Act records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import sqlite3

from app.services.logging_service import log_activity

VALID_SEVERITIES = ("Critical", "High", "Medium", "Low")
VALID_STATUSES = ("Reported", "Investigating", "Fix Implemented", "Verified", "Closed")


# ------------------------------------------------------------------------------
# 1. Defect Checksheet & Lifecycle
# ------------------------------------------------------------------------------

def get_defects(
    conn: sqlite3.Connection,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    module: Optional[str] = None,
    search: Optional[str] = None,
) -> List[sqlite3.Row]:
    """Retrieve filtered defect records.

    Args:
        conn: SQLite connection.
        status: Filter by status.
        severity: Filter by severity.
        module: Filter by module name.
        search: Filter by keyword in description or defect code.

    Returns:
        List[sqlite3.Row]: Matching defect rows ordered by ID descending.
    """
    conditions = []
    params: List[Any] = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if severity:
        conditions.append("severity = ?")
        params.append(severity)
    if module:
        conditions.append("affected_module = ?")
        params.append(module)
    if search:
        conditions.append("(defect_code LIKE ? OR description LIKE ? OR category LIKE ?)")
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM quality_defects{where_clause} ORDER BY id DESC",
        params,
    )
    return cursor.fetchall()


def get_defect_by_id(conn: sqlite3.Connection, defect_id: int) -> Optional[sqlite3.Row]:
    """Retrieve single defect by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quality_defects WHERE id = ?", (defect_id,))
    return cursor.fetchone()


def generate_defect_code(conn: sqlite3.Connection) -> str:
    """Generate sequential defect code (e.g. DEF-008)."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM quality_defects ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    next_id = (row["id"] + 1) if row else 1
    return f"DEF-{next_id:03d}"


def create_defect(
    conn: sqlite3.Connection,
    affected_module: str,
    description: str,
    category: str,
    severity: str,
    root_cause_category: str,
    occurrence_count: int = 1,
    corrective_action: Optional[str] = None,
    actor: str = "Quality Lead",
) -> int:
    """Record a new defect into the checksheet register.

    Args:
        conn: SQLite connection.
        affected_module: Affected subsystem.
        description: Specific malfunction description.
        category: Defect classification.
        severity: 'Critical', 'High', 'Medium', 'Low'.
        root_cause_category: Ishikawa root cause category.
        occurrence_count: Number of observed instances.
        corrective_action: Proposed or implemented fix.
        actor: Reporter.

    Returns:
        int: Primary key ID of created defect.
    """
    if not affected_module or not description or not category:
        raise ValueError("Module, description, and category are required fields.")

    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity '{severity}'. Must be one of {VALID_SEVERITIES}.")

    if occurrence_count <= 0:
        raise ValueError("Occurrence count must be at least 1.")

    code = generate_defect_code(conn)
    now = datetime.now(timezone.utc).isoformat()
    today = datetime.now().strftime("%Y-%m-%d")

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO quality_defects (
            defect_code, date_reported, affected_module, description, category,
            severity, occurrence_count, root_cause_category, corrective_action,
            status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Reported', ?, ?)
        """,
        (
            code,
            today,
            affected_module.strip(),
            description.strip(),
            category.strip(),
            severity,
            occurrence_count,
            root_cause_category.strip(),
            corrective_action.strip() if corrective_action else None,
            now,
            now,
        ),
    )
    conn.commit()
    defect_id = cursor.lastrowid

    log_activity(
        conn=conn,
        action_type="DEFECT_REPORT",
        module="Quality",
        description=f"Reported {severity} defect {code} in {affected_module}: {description[:50]}",
        actor=actor,
        affected_record_id=code,
        outcome="Warning" if severity in ("Critical", "High") else "Success",
    )
    return defect_id


def update_defect_status(
    conn: sqlite3.Connection,
    defect_id: int,
    new_status: str,
    corrective_action: Optional[str] = None,
    actor: str = "Quality Lead",
) -> None:
    """Transition defect through lifecycle (Reported -> Investigating -> Fix Implemented -> Verified -> Closed)."""
    defect = get_defect_by_id(conn, defect_id)
    if not defect:
        raise ValueError(f"Defect #{defect_id} not found.")

    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {VALID_STATUSES}.")

    now = datetime.now(timezone.utc).isoformat()
    res_date = datetime.now().strftime("%Y-%m-%d") if new_status in ("Verified", "Closed") else None

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE quality_defects
        SET status = ?, corrective_action = COALESCE(?, corrective_action),
            resolution_date = COALESCE(?, resolution_date), updated_at = ?
        WHERE id = ?
        """,
        (new_status, corrective_action, res_date, now, defect_id),
    )
    conn.commit()

    log_activity(
        conn=conn,
        action_type="DEFECT_STATUS_UPDATE",
        module="Quality",
        description=f"Updated defect {defect['defect_code']} status to '{new_status}'",
        actor=actor,
        affected_record_id=defect["defect_code"],
        outcome="Success",
    )


# ------------------------------------------------------------------------------
# 2. Pareto Analysis Calculation
# ------------------------------------------------------------------------------

def calculate_pareto_analysis(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Generate Pareto dataset and mathematical statistics from actual defect records.

    Groups defects by category, aggregates occurrence counts, sorts in descending order,
    and computes cumulative counts and cumulative percentages.

    Returns:
        Dict[str, Any]: Formatted data for Chart.js rendering and empirical analysis.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT category, SUM(occurrence_count) AS total_occurrences, COUNT(*) AS defect_count
        FROM quality_defects
        GROUP BY category
        ORDER BY total_occurrences DESC
        """
    )
    rows = cursor.fetchall()

    if not rows:
        return {
            "has_data": False,
            "labels": [],
            "counts": [],
            "cumulative_percentages": [],
            "vital_few": [],
            "summary_text": "No quality defect data recorded yet. Please add defect observations to generate Pareto analysis.",
        }

    total_sum = sum(row["total_occurrences"] for row in rows)
    labels = []
    counts = []
    cum_percentages = []
    running_sum = 0
    vital_few = []

    for row in rows:
        cat = row["category"]
        cnt = row["total_occurrences"]
        running_sum += cnt
        pct = round((running_sum / total_sum) * 100.0, 1) if total_sum > 0 else 0.0

        labels.append(cat)
        counts.append(cnt)
        cum_percentages.append(pct)

        # Categorize under 80% threshold as "vital few"
        if pct <= 80.0 or len(vital_few) == 0:
            vital_few.append(cat)

    summary_text = (
        f"Pareto analysis of {total_sum} defect occurrences across {len(rows)} categories reveals that "
        f"'{', '.join(vital_few)}' constitute the primary drivers of system defects. "
        f"Addressing these vital few categories will yield maximum quality improvement per TQM principles."
    )

    return {
        "has_data": True,
        "labels": labels,
        "counts": counts,
        "cumulative_percentages": cum_percentages,
        "total_occurrences": total_sum,
        "vital_few": vital_few,
        "summary_text": summary_text,
    }


# ------------------------------------------------------------------------------
# 3. FMEA (Failure Mode and Effects Analysis)
# ------------------------------------------------------------------------------

def get_fmea_records(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """Retrieve FMEA entries ordered by Risk Priority Number (RPN) descending."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, process_step, potential_failure_mode, potential_effect, potential_cause,
               existing_controls, severity, occurrence, detection,
               (severity * occurrence * detection) AS rpn,
               recommended_mitigation, responsible_role, status, updated_at
        FROM fmea_records
        ORDER BY rpn DESC
        """
    )
    return cursor.fetchall()


def add_fmea_record(
    conn: sqlite3.Connection,
    process_step: str,
    potential_failure_mode: str,
    potential_effect: str,
    potential_cause: str,
    existing_controls: str,
    severity: int,
    occurrence: int,
    detection: int,
    recommended_mitigation: str,
    responsible_role: str,
) -> int:
    """Create a new FMEA failure mode assessment.

    Args:
        severity: Rating 1-10.
        occurrence: Rating 1-10.
        detection: Rating 1-10.
    """
    for val, name in [(severity, "Severity"), (occurrence, "Occurrence"), (detection, "Detection")]:
        if not (1 <= val <= 10):
            raise ValueError(f"{name} rating must be an integer between 1 and 10.")

    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO fmea_records (
            process_step, potential_failure_mode, potential_effect, potential_cause,
            existing_controls, severity, occurrence, detection,
            recommended_mitigation, responsible_role, status, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
        """,
        (
            process_step.strip(),
            potential_failure_mode.strip(),
            potential_effect.strip(),
            potential_cause.strip(),
            existing_controls.strip(),
            severity,
            occurrence,
            detection,
            recommended_mitigation.strip(),
            responsible_role.strip(),
            now,
        ),
    )
    conn.commit()
    return cursor.lastrowid


# ------------------------------------------------------------------------------
# 4. Ishikawa / Fishbone Diagram Data Structure
# ------------------------------------------------------------------------------

def get_fishbone_causes() -> Dict[str, List[Dict[str, Any]]]:
    """Return categorized root-cause taxonomy across 6 standard TQM dimensions."""
    return {
        "People": [
            {"cause": "Cashier inattentive to discount input boundaries", "status": "Hypothesis"},
            {"cause": "Insufficient training on invoice cancellation workflow", "status": "Hypothesis"},
            {"cause": "Staff overriding table assignments during peak hours", "status": "Verified"},
        ],
        "Process": [
            {"cause": "Unclear discount approval authorization workflow", "status": "Verified"},
            {"cause": "Absence of double-check step before bill printing", "status": "Verified"},
            {"cause": "Order status transition allowed while items in cart", "status": "Mitigated"},
        ],
        "Software Code": [
            {"cause": "Floating-point IEEE-754 precision rounding errors in tax math", "status": "Mitigated"},
            {"cause": "Non-atomic invoice finalization under concurrent clicks", "status": "Mitigated"},
            {"cause": "Duplicated billing calculation formulas across views", "status": "Mitigated"},
        ],
        "Database": [
            {"cause": "Missing SQLite PRAGMA foreign_keys = ON on connection", "status": "Mitigated"},
            {"cause": "Absence of UNIQUE constraint on invoice numbers", "status": "Mitigated"},
            {"cause": "Dynamic joins on live menu table silently corrupting past receipts", "status": "Mitigated"},
        ],
        "Testing": [
            {"cause": "Absence of boundary value test cases for discount ceiling", "status": "Mitigated"},
            {"cause": "Lack of automated test isolation using temporary database", "status": "Mitigated"},
            {"cause": "Missing regression tests for tax changes", "status": "Mitigated"},
        ],
        "Infrastructure": [
            {"cause": "Sudden terminal/power termination during write operations", "status": "Mitigated (WAL mode)"},
            {"cause": "Log files consuming disk storage without log rotation", "status": "Mitigated (RotatingFileHandler)"},
            {"cause": "Hardcoded file paths failing across operating systems", "status": "Mitigated (Pathlib)"},
        ],
    }


# ------------------------------------------------------------------------------
# 5. PDCA Continuous Improvement Register
# ------------------------------------------------------------------------------

def get_pdca_cycles(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """Retrieve all continuous improvement cycles."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quality_improvements ORDER BY id ASC")
    return cursor.fetchall()


# ------------------------------------------------------------------------------
# 6. Quality Dashboard Statistics
# ------------------------------------------------------------------------------

def get_quality_summary_metrics(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Calculate aggregated TQM metrics from actual database tables.

    Returns:
        Dict[str, Any]: Real calculated counts (Total, Open, Resolved, Severity Breakdown, PDCA status).
    """
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM quality_defects")
    total_defects = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS open_cnt FROM quality_defects WHERE status IN ('Reported', 'Investigating')"
    )
    open_defects = cursor.fetchone()["open_cnt"]

    cursor.execute(
        "SELECT COUNT(*) AS res_cnt FROM quality_defects WHERE status IN ('Fix Implemented', 'Verified', 'Closed')"
    )
    resolved_defects = cursor.fetchone()["res_cnt"]

    cursor.execute(
        "SELECT severity, COUNT(*) AS cnt FROM quality_defects GROUP BY severity"
    )
    severity_breakdown = {row["severity"]: row["cnt"] for row in cursor.fetchall()}

    cursor.execute(
        "SELECT affected_module, COUNT(*) AS cnt FROM quality_defects GROUP BY affected_module"
    )
    module_breakdown = {row["affected_module"]: row["cnt"] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) AS pdca_cnt FROM quality_improvements WHERE status = 'Completed'")
    completed_improvements = cursor.fetchone()["pdca_cnt"]

    cursor.execute("SELECT MAX(severity * occurrence * detection) AS max_rpn FROM fmea_records")
    row_max_rpn = cursor.fetchone()
    max_rpn = row_max_rpn["max_rpn"] if row_max_rpn and row_max_rpn["max_rpn"] else 0

    return {
        "total_defects": total_defects,
        "open_defects": open_defects,
        "resolved_defects": resolved_defects,
        "resolution_rate_percent": round((resolved_defects / total_defects * 100), 1) if total_defects > 0 else 0.0,
        "severity_breakdown": severity_breakdown,
        "module_breakdown": module_breakdown,
        "completed_improvements": completed_improvements,
        "max_rpn": max_rpn,
    }

"""Logging Service for Dual-Layer Audit & Diagnostic Logs.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides:
1. Technical Diagnostic Logging via Python standard logging and RotatingFileHandler.
2. Business Activity Audit Trail stored in SQLite table 'activity_logs'.
3. Sanitization to prevent sensitive data/passwords from ever entering logs.
4. Search, filtering, and pagination for administrator review.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sqlite3

# Sensitive key substrings that must be redacted
SENSITIVE_KEYS = {"password", "secret", "token", "auth", "credit_card", "cvv"}

# Global application logger instance
_app_logger: Optional[logging.Logger] = None


def setup_application_logger(
    log_file: str = "logs/app.log",
    log_level: str = "INFO",
    max_bytes: int = 1048576,
    backup_count: int = 5,
) -> logging.Logger:
    """Initialize and configure the rotating file logger for technical diagnostics.

    Args:
        log_file: Path to destination log file.
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_bytes: Maximum size of single log file before rotation.
        backup_count: Number of rotated backup files to retain.

    Returns:
        logging.Logger: Configured logger.
    """
    global _app_logger
    logger = logging.getLogger("rbs_technical")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Prevent duplicate handlers when re-initializing
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s"
    )

    # File handler with automatic rotation
    file_handler = RotatingFileHandler(
        str(log_path), maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler for local terminal visibility
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _app_logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Retrieve the application technical logger instance."""
    global _app_logger
    if _app_logger is None:
        _app_logger = setup_application_logger()
    return _app_logger


def sanitize_message(data: Any) -> Any:
    """Recursively redact sensitive key-values from logged structures.

    Args:
        data: Primitive, dict, or list data to sanitize.

    Returns:
        Sanitized structure with sensitive values replaced by '[REDACTED]'.
    """
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(s in str(k).lower() for s in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_message(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_message(item) for item in data]
    return data


def log_activity(
    conn: sqlite3.Connection,
    action_type: str,
    module: str,
    description: str,
    actor: str = "Staff",
    affected_record_id: Optional[str] = None,
    outcome: str = "Success",
    correlation_id: Optional[str] = None,
) -> int:
    """Record a business event into the SQLite activity_logs audit table.

    Also mirrors diagnostic warning or error to rotating technical log.

    Args:
        conn: SQLite connection.
        action_type: Category of action (e.g., 'MENU_CREATE', 'INVOICE_FINALIZE').
        module: Subsystem name (e.g., 'Menu', 'Billing', 'Settings').
        description: Readable summary of the business action.
        actor: Identity of actor performing the action.
        affected_record_id: Unique identifier of affected record.
        outcome: Result ('Success', 'Failure', 'Warning').
        correlation_id: Optional request or correlation identifier.

    Returns:
        int: Primary key ID of the newly created audit log entry.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO activity_logs (
            timestamp, actor, action_type, module, affected_record_id, outcome, description, correlation_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (timestamp, actor, action_type, module, affected_record_id, outcome, description, correlation_id),
    )
    conn.commit()
    log_id = cursor.lastrowid

    # Mirror to technical logger
    tech_logger = get_logger()
    log_msg = f"[{outcome}] [{module}] {action_type} - {description} (Record: {affected_record_id}, Actor: {actor})"
    if outcome == "Failure":
        tech_logger.error(log_msg)
    elif outcome == "Warning":
        tech_logger.warning(log_msg)
    else:
        tech_logger.info(log_msg)

    return log_id


def get_activity_logs(
    conn: sqlite3.Connection,
    module: Optional[str] = None,
    outcome: Optional[str] = None,
    action_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 15,
) -> Tuple[List[sqlite3.Row], int]:
    """Retrieve filtered, paginated activity logs for administrative inspection.

    Args:
        conn: SQLite connection.
        module: Optional filter by subsystem module.
        outcome: Optional filter by outcome status.
        action_type: Optional filter by action type.
        search: Optional text search in description or affected_record_id.
        page: Page number (1-indexed).
        per_page: Number of items per page.

    Returns:
        Tuple[List[sqlite3.Row], int]: List of log records and total record count.
    """
    conditions = []
    params: List[Any] = []

    if module:
        conditions.append("module = ?")
        params.append(module)
    if outcome:
        conditions.append("outcome = ?")
        params.append(outcome)
    if action_type:
        conditions.append("action_type = ?")
        params.append(action_type)
    if search:
        conditions.append("(description LIKE ? OR affected_record_id LIKE ? OR actor LIKE ?)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    cursor = conn.cursor()
    count_query = f"SELECT COUNT(*) AS total FROM activity_logs{where_clause}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()["total"]

    offset = max(0, (page - 1) * per_page)
    data_query = f"""
        SELECT * FROM activity_logs{where_clause}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(data_query, params + [per_page, offset])
    rows = cursor.fetchall()

    return rows, total_count

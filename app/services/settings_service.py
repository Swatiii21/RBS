"""System Settings Service for Dynamic UI Configuration.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Eliminates hardcoded business parameters by enabling authorized administrative users
to view and edit restaurant profile, billing policies, UI display options, and logging
configurations with strict server-side validation and audit logging.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import sqlite3

from app.services.logging_service import log_activity


# Cache for in-process fast reads; invalidated upon update
_SETTINGS_CACHE: Dict[str, str] = {}


def load_settings_dict(conn: sqlite3.Connection) -> Dict[str, str]:
    """Retrieve all current system settings from database as a flat key-value dictionary.

    Args:
        conn: SQLite connection.

    Returns:
        Dict[str, str]: Dictionary mapping setting key to current string value.
    """
    global _SETTINGS_CACHE
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM system_settings")
    rows = cursor.fetchall()
    _SETTINGS_CACHE = {row["key"]: row["value"] for row in rows}
    return dict(_SETTINGS_CACHE)


def get_setting(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    """Retrieve a single configuration setting by key.

    Args:
        conn: SQLite connection.
        key: Setting key name.
        default: Fallback value if setting key does not exist.

    Returns:
        Value converted or string, or fallback default.
    """
    global _SETTINGS_CACHE
    if not _SETTINGS_CACHE:
        load_settings_dict(conn)

    val = _SETTINGS_CACHE.get(key)
    if val is None:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            val = row["value"]
            _SETTINGS_CACHE[key] = val
        else:
            return default
    return val


def get_grouped_settings(conn: sqlite3.Connection) -> Dict[str, List[sqlite3.Row]]:
    """Retrieve all settings grouped by functional section.

    Sections: 'restaurant_profile', 'billing_settings', 'application_settings', 'logging_settings'

    Args:
        conn: SQLite connection.

    Returns:
        Dict[str, List[sqlite3.Row]]: Grouped rows for settings UI page rendering.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM system_settings ORDER BY section, key")
    rows = cursor.fetchall()

    grouped: Dict[str, List[sqlite3.Row]] = {}
    for row in rows:
        sec = row["section"]
        if sec not in grouped:
            grouped[sec] = []
        grouped[sec].append(row)
    return grouped


def validate_setting_value(key: str, value: str) -> None:
    """Perform strict server-side validation on setting updates.

    Args:
        key: The setting name.
        value: The user-supplied new value.

    Raises:
        ValueError: If the supplied value violates boundary constraints.
    """
    if key in ("default_tax_rate", "max_discount_percentage"):
        try:
            num = float(value)
            if num < 0.0 or num > 100.0:
                raise ValueError(f"Setting '{key}' must be a percentage between 0 and 100, got {value}.")
        except ValueError as err:
            if "must be a percentage" in str(err):
                raise
            raise ValueError(f"Setting '{key}' must be a valid numeric decimal number.") from err

    elif key == "default_page_size":
        try:
            num = int(value)
            if num < 5 or num > 100:
                raise ValueError("Default page size must be an integer between 5 and 100.")
        except ValueError as err:
            raise ValueError("Default page size must be a valid integer.") from err

    elif key in ("restaurant_name", "contact_number", "address"):
        if not value or not value.strip():
            raise ValueError(f"Field '{key.replace('_', ' ').title()}' cannot be empty.")

    elif key == "rounding_policy":
        valid_policies = {"ROUND_HALF_UP", "ROUND_CEIL", "ROUND_FLOOR"}
        if value not in valid_policies:
            raise ValueError(f"Rounding policy must be one of {valid_policies}.")

    elif key == "min_log_level":
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value.upper() not in valid_levels:
            raise ValueError(f"Minimum log level must be one of {valid_levels}.")


def update_setting(
    conn: sqlite3.Connection,
    key: str,
    value: str,
    updated_by: str = "Administrator",
) -> None:
    """Validate and update a single system setting, logging an audit trail.

    Args:
        conn: SQLite connection.
        key: Setting key.
        value: New string value.
        updated_by: Name or role of updating user.

    Raises:
        ValueError: If validation fails.
    """
    validate_setting_value(key, value)
    now = datetime.now(timezone.utc).isoformat()

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE system_settings
        SET value = ?, updated_by = ?, updated_at = ?
        WHERE key = ?
        """,
        (value.strip(), updated_by, now, key),
    )
    conn.commit()

    # Invalidate cache
    global _SETTINGS_CACHE
    _SETTINGS_CACHE[key] = value.strip()

    # Audit log
    log_activity(
        conn=conn,
        action_type="SETTINGS_UPDATE",
        module="Settings",
        description=f"Updated setting '{key}' to '{value}'",
        actor=updated_by,
        affected_record_id=key,
        outcome="Success",
    )


def update_settings_batch(
    conn: sqlite3.Connection,
    updates: Dict[str, str],
    updated_by: str = "Administrator",
) -> List[str]:
    """Validate and update multiple settings atomically.

    Args:
        conn: SQLite connection.
        updates: Key-value map of settings to update.
        updated_by: Name or role of updating user.

    Returns:
        List[str]: List of keys successfully updated.

    Raises:
        ValueError: If any single setting fails validation before writing.
    """
    # Pre-validate all updates to guarantee atomicity
    for key, val in updates.items():
        validate_setting_value(key, str(val))

    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    changed_keys = []

    for key, val in updates.items():
        clean_val = str(val).strip()
        cursor.execute(
            """
            UPDATE system_settings
            SET value = ?, updated_by = ?, updated_at = ?
            WHERE key = ?
            """,
            (clean_val, updated_by, now, key),
        )
        changed_keys.append(key)
        _SETTINGS_CACHE[key] = clean_val

    conn.commit()

    log_activity(
        conn=conn,
        action_type="SETTINGS_BATCH_UPDATE",
        module="Settings",
        description=f"Batch updated {len(changed_keys)} settings: {', '.join(changed_keys)}",
        actor=updated_by,
        affected_record_id="batch",
        outcome="Success",
    )

    return changed_keys

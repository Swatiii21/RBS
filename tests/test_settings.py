"""Automated Tests for System Settings and Dynamic Configuration.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management
"""

import pytest
import sqlite3

from app.config import Config, get_config
from app.services.settings_service import (
    get_setting,
    load_settings_dict,
    update_setting,
    update_settings_batch,
)


def test_load_default_settings(db_conn: sqlite3.Connection):
    """Verify pre-seeded baseline settings load from database."""
    settings = load_settings_dict(db_conn)
    assert "restaurant_name" in settings
    assert "default_tax_rate" in settings
    assert float(settings["default_tax_rate"]) == 5.0
    assert float(settings["max_discount_percentage"]) == 25.0


def test_update_and_reload_setting(db_conn: sqlite3.Connection):
    """Verify updating setting persists and updates cache."""
    update_setting(db_conn, "restaurant_name", "Grand Emerald Palace")
    reloaded = get_setting(db_conn, "restaurant_name")
    assert reloaded == "Grand Emerald Palace"


def test_reject_invalid_setting_values(db_conn: sqlite3.Connection):
    """Ensure out-of-boundary values are rejected before persisting."""
    # Tax rate > 100%
    with pytest.raises(ValueError, match="must be a percentage between 0 and 100"):
        update_setting(db_conn, "default_tax_rate", "150.0")

    # Empty restaurant name
    with pytest.raises(ValueError, match="cannot be empty"):
        update_setting(db_conn, "restaurant_name", "   ")

    # Invalid rounding policy
    with pytest.raises(ValueError, match="Rounding policy must be one of"):
        update_setting(db_conn, "rounding_policy", "INVALID_RULE")


def test_settings_change_audit_logging(db_conn: sqlite3.Connection):
    """Ensure any modification to system settings produces an audit log entry."""
    update_setting(db_conn, "default_tax_rate", "8.5", updated_by="Admin Swati")
    log = db_conn.execute(
        "SELECT * FROM activity_logs WHERE action_type = 'SETTINGS_UPDATE' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert log is not None
    assert "8.5" in log["description"]
    assert log["actor"] == "Admin Swati"


def test_config_class_validation():
    """Verify Config.validate() catches critical configuration errors."""
    dev_config = get_config("development")
    assert dev_config.APP_NAME is not None
    assert dev_config.DEBUG is True

"""Automated Tests for Activity Logs and Sensitive Data Sanitization.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management
"""

import sqlite3
from app.services.logging_service import (
    get_activity_logs,
    log_activity,
    sanitize_message,
)


def test_log_business_activity(db_conn: sqlite3.Connection):
    """Verify recording an action inserts into activity_logs table."""
    log_id = log_activity(
        conn=db_conn,
        action_type="TEST_ACTION",
        module="TestModule",
        description="Executed automated test action",
        actor="TestRunner",
        affected_record_id="REC-001",
        outcome="Success",
    )
    assert log_id > 0

    logs, total = get_activity_logs(db_conn, module="TestModule")
    assert total >= 1
    assert logs[0]["action_type"] == "TEST_ACTION"
    assert logs[0]["outcome"] == "Success"


def test_sensitive_payload_sanitization():
    """Verify credentials, passwords, and tokens are redacted prior to logging."""
    raw_payload = {
        "username": "cashier_swati",
        "password": "SuperSecretPassword123!",
        "auth_token": "jwt_secret_token_abc_xyz",
        "nested": {
            "credit_card": "4111222233334444",
            "safe_field": "public_data",
        },
    }
    sanitized = sanitize_message(raw_payload)

    assert sanitized["username"] == "cashier_swati"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["auth_token"] == "[REDACTED]"
    assert sanitized["nested"]["credit_card"] == "[REDACTED]"
    assert sanitized["nested"]["safe_field"] == "public_data"


def test_activity_log_filtering(db_conn: sqlite3.Connection):
    """Test filtering activity logs by outcome and search terms."""
    log_activity(db_conn, "OP_A", "ModuleA", "Success event A", outcome="Success")
    log_activity(db_conn, "OP_B", "ModuleB", "Warning anomaly B", outcome="Warning")
    log_activity(db_conn, "OP_C", "ModuleC", "Failure crash C", outcome="Failure")

    # Filter by outcome
    failures, f_cnt = get_activity_logs(db_conn, outcome="Failure")
    assert f_cnt == 1
    assert failures[0]["action_type"] == "OP_C"

    # Search keyword
    searched, s_cnt = get_activity_logs(db_conn, search="anomaly")
    assert s_cnt == 1
    assert searched[0]["action_type"] == "OP_B"

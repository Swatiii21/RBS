"""Database Initialization, Migration, and Seed Utilities.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides idempotent schema creation and initial data seeding for:
- System settings (Restaurant Profile, Billing Settings, App Settings, Logging Settings)
- Realistic multi-category menu items
- Realistic TQM Quality Defects (for Pareto and Defect Checksheet demonstration)
- Realistic FMEA entries (with RPN calculations)
- Realistic PDCA continuous improvement cycle records
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Optional

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
EXAMPLE_SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "settings.example.json"


def init_db(conn: sqlite3.Connection) -> None:
    """Execute schema.sql to ensure all required tables and indexes exist.

    Args:
        conn: SQLite connection.
    """
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()


def seed_default_settings(conn: sqlite3.Connection) -> None:
    """Seed initial system settings if not already present.

    Args:
        conn: SQLite connection.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS cnt FROM system_settings")
    if cursor.fetchone()["cnt"] > 0:
        return  # Settings already seeded

    now = datetime.now(timezone.utc).isoformat()
    default_settings = [
        # Restaurant Profile
        ("restaurant_name", "Emerald Dine Restaurant", "restaurant_profile", "Official Restaurant Name", "System", now),
        ("address", "124 Parkview Avenue, Civil Lines, Dehradun, Uttarakhand - 248001", "restaurant_profile", "Physical address for invoice header", "System", now),
        ("contact_number", "+91 98765 43210", "restaurant_profile", "Customer support / reservations phone number", "System", now),
        ("email", "contact@emeralddine.com", "restaurant_profile", "Billing & correspondence email", "System", now),
        ("invoice_footer_text", "Thank you for dining with us! Please visit again. Total Quality Management Certified.", "restaurant_profile", "Printed message at invoice bottom", "System", now),

        # Billing Settings
        ("currency_symbol", "₹", "billing_settings", "Currency symbol for display and invoices", "System", now),
        ("default_tax_rate", "5.0", "billing_settings", "Default applicable tax rate percentage", "System", now),
        ("max_discount_percentage", "25.0", "billing_settings", "Maximum permitted discount threshold", "System", now),
        ("invoice_prefix", "INV-", "billing_settings", "Prefix string for invoice numbering", "System", now),
        ("invoice_numbering_policy", "SEQUENTIAL_YEAR", "billing_settings", "Invoice sequence numbering format", "System", now),
        ("rounding_policy", "ROUND_HALF_UP", "billing_settings", "Mathematical rounding rule for totals", "System", now),

        # Application Settings
        ("app_name", "Restaurant Billing System — Q11", "application_settings", "Application display title", "System", now),
        ("default_page_size", "15", "application_settings", "Default number of records per page", "System", now),
        ("date_format", "%Y-%m-%d", "application_settings", "Display date format", "System", now),
        ("time_format", "%H:%M:%S", "application_settings", "Display time format", "System", now),
        ("activity_log_retention_days", "90", "application_settings", "Days before archiving activity logs", "System", now),

        # Logging Settings
        ("min_log_level", "INFO", "logging_settings", "Minimum severity level for logging", "System", now),
        ("log_retention_duration_days", "30", "logging_settings", "Retention period for rotating logs", "System", now),
        ("log_successful_actions", "true", "logging_settings", "Whether to audit successful business actions", "System", now),
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO system_settings (key, value, section, description, updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        default_settings,
    )
    conn.commit()


def seed_sample_menu(conn: sqlite3.Connection) -> None:
    """Seed standard realistic restaurant menu items.

    Args:
        conn: SQLite connection.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS cnt FROM menu_items")
    if cursor.fetchone()["cnt"] > 0:
        return

    now = datetime.now(timezone.utc).isoformat()
    menu_items = [
        ("M-101", "Paneer Butter Masala", "Main Course", "Rich cottage cheese cubes simmered in a buttery tomato gravy", 280.00, 1, now, now),
        ("M-102", "Dal Makhani", "Main Course", "Slow-cooked black lentils with fresh cream and butter", 240.00, 1, now, now),
        ("M-103", "Kadhai Paneer", "Main Course", "Cottage cheese sauteed with bell peppers and freshly ground spices", 270.00, 1, now, now),
        ("M-104", "Butter Chicken", "Main Course", "Tender roasted chicken cooked in a smooth, mild tomato gravy", 340.00, 1, now, now),
        ("M-105", "Crispy Corn & Pepper", "Starters", "Golden crispy sweet corn tossed with chili flakes and spring onion", 180.00, 1, now, now),
        ("M-106", "Paneer Tikka", "Starters", "Char-grilled marinated cottage cheese cubes with mint dip", 230.00, 1, now, now),
        ("M-107", "Chicken Malai Tikka", "Starters", "Succulent chicken morsels marinated in cream and mild herbs", 290.00, 1, now, now),
        ("M-108", "Garlic Butter Naan", "Breads", "Freshly baked leavened bread brushed with garlic butter", 60.00, 1, now, now),
        ("M-109", "Tandoori Roti", "Breads", "Traditional whole wheat bread baked in clay tandoor", 30.00, 1, now, now),
        ("M-110", "Jeera Rice", "Rice", "Aromatic basmati rice tempered with roasted cumin seeds", 140.00, 1, now, now),
        ("M-111", "Fresh Lime Soda", "Beverages", "Refreshing lemon juice with sweet and salted sparkling soda", 80.00, 1, now, now),
        ("M-112", "Masala Chai", "Beverages", "Handcrafted Indian spiced tea with cardamom and ginger", 50.00, 1, now, now),
        ("M-113", "Gulab Jamun (2 Pcs)", "Desserts", "Warm golden dumplings soaked in saffron-scented sugar syrup", 90.00, 1, now, now),
        ("M-114", "Vanilla Bean Ice Cream", "Desserts", "Classic rich vanilla ice cream topped with chocolate drizzle", 110.00, 1, now, now),
    ]

    cursor.executemany(
        """
        INSERT INTO menu_items (item_code, name, category, description, unit_price, is_available, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        menu_items,
    )
    conn.commit()


def seed_tqm_sample_data(conn: sqlite3.Connection) -> None:
    """Seed sample TQM quality records (Defects, FMEA, PDCA) for live demo.

    Args:
        conn: SQLite connection.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS cnt FROM quality_defects")
    if cursor.fetchone()["cnt"] == 0:
        now = datetime.now(timezone.utc).isoformat()
        sample_defects = [
            ("DEF-001", "2026-10-01", "Billing", "Tax calculation rounding differed by 1 paisa when multiple discounts were applied", "Calculation Error", "Medium", 8, "Rounding Logic", "Implemented Decimal-based quantize rounding with ROUND_HALF_UP", "Verified", "2026-10-03", now, now),
            ("DEF-002", "2026-10-03", "Order Management", "Browser allowed user to enter negative discount percentage in discount input", "Input Validation", "High", 14, "Missing Server Check", "Added strict server-side validation rejecting discount < 0 or > configured limit", "Closed", "2026-10-04", now, now),
            ("DEF-003", "2026-10-05", "Menu Management", "Attempted to delete menu item that had historical orders without cascade safety", "Data Integrity", "Critical", 3, "Database Constraint", "Updated foreign key constraint to ON DELETE SET NULL and restricted deletion in service", "Closed", "2026-10-06", now, now),
            ("DEF-004", "2026-10-07", "Billing", "Rapid double-click on 'Finalize Bill' button created duplicate invoice numbers", "Concurrency/Transaction", "High", 7, "Missing Idempotency", "Wrapped invoice finalization in ACID transaction with unique constraint check", "Closed", "2026-10-08", now, now),
            ("DEF-005", "2026-10-09", "System Settings", "Changing tax rate through admin UI required web server restart to reflect in new bills", "Maintainability/Config", "Medium", 6, "Static Cache", "Refactored settings_service to reload values dynamically from database cache", "Verified", "2026-10-10", now, now),
            ("DEF-006", "2026-10-11", "Activity Logs", "Staff password attempted to log in clear text during failed login event", "Security/Audit", "Critical", 1, "Logging Filter", "Sanitized log payloads to redact sensitive credential keys", "Closed", "2026-10-11", now, now),
            ("DEF-007", "2026-10-12", "Billing History", "Search by date filter threw ValueError when date format was entered as DD/MM/YYYY", "Input Validation", "Low", 5, "Format Mismatch", "Normalized all query date inputs to ISO format YYYY-MM-DD", "Investigating", None, now, now),
        ]
        cursor.executemany(
            """
            INSERT INTO quality_defects (defect_code, date_reported, affected_module, description, category, severity, occurrence_count, root_cause_category, corrective_action, status, resolution_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sample_defects,
        )

    cursor.execute("SELECT COUNT(*) AS cnt FROM fmea_records")
    if cursor.fetchone()["cnt"] == 0:
        now = datetime.now(timezone.utc).isoformat()
        sample_fmea = [
            ("Billing Calculation", "Incorrect tax calculation on discounted items", "Customer overcharged or undercharged; regulatory compliance risk", "Tax calculated before deducting promotional discount", "Client-side JS math script", 7, 5, 4, "Centralized Decimal calculation service with server-side validation", "Backend Lead", "Mitigated", now),
            ("Invoice Finalization", "Duplicate invoice number generated under concurrency", "Financial ledger inconsistency and duplicate customer bills", "Non-transactional sequence generation", "Application-level counter", 8, 4, 3, "ACID transaction with immediate lock and database unique constraint", "Database Architect", "Mitigated", now),
            ("Order Management", "Negative quantity or negative price submitted", "Negative bill totals leading to restaurant revenue loss", "Absence of server-side boundary checks", "HTML5 input min attribute", 8, 6, 2, "Server-side validator rejecting quantity <= 0 and price < 0", "Security/QA Lead", "Mitigated", now),
            ("Menu Management", "Menu price update silently changes totals of already finalized past orders", "Corrupted historical financial reports and auditing failure", "Historical order items referencing live menu table dynamically", "Relational foreign key join", 9, 3, 3, "Snapshot item_name and unit_price directly into order_items table", "System Designer", "Mitigated", now),
            ("System Settings", "Invalid tax rate (e.g. 150%) saved by administrator", "System produces absurd invoices, crashes billing calculation", "Unvalidated settings form inputs", "None", 6, 4, 3, "Server-side range validation (0 <= tax_rate <= 100) before DB commit", "Admin Lead", "Mitigated", now),
        ]
        cursor.executemany(
            """
            INSERT INTO fmea_records (process_step, potential_failure_mode, potential_effect, potential_cause, existing_controls, severity, occurrence, detection, recommended_mitigation, responsible_role, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sample_fmea,
        )

    cursor.execute("SELECT COUNT(*) AS cnt FROM quality_improvements")
    if cursor.fetchone()["cnt"] == 0:
        now = datetime.now(timezone.utc).isoformat()
        sample_pdca = [
            ("PDCA-01", "Prevent Invalid Discount Rates via Server Validation",
             "Customers received discounts exceeding restaurant margin (up to 99%) due to client-side manipulation.",
             "Restrict discounts strictly to configured ceiling (max 25%) with zero bypass tolerance.",
             "Implement server-side validator in billing_service.py and display descriptive error message.",
             "Added validate_discount() in billing_service.py; linked to DEF-002.",
             "DEF-002",
             "100 automated test submissions with discount > 25% were rejected with HTTP 400 Bad Request.",
             "Defect occurrence dropped from 14 occurrences to 0 in testing phase.",
             "Accepted",
             "Never trust browser form inputs for financial limits. Always enforce limits in core business logic.",
             "Swati Melkani",
             "2026-10-15",
             "Completed",
             now),
            ("PDCA-02", "ACID Transaction Protection for Invoice Finalization",
             "Network glitch during finalization left order marked finalized without generating invoice record.",
             "Ensure order status update and invoice record creation succeed together or rollback completely.",
             "Wrap finalization in database connection transaction context manager with rollback on failure.",
             "Implemented transaction(conn) in connection.py and billing_service.py; linked to DEF-004.",
             "DEF-004",
             "Simulated power interruption/exception inside transaction. Both order and invoice rolled back safely.",
             "Zero orphan finalized orders observed during stress testing.",
             "Accepted",
             "Financial status transitions must always be transactional.",
             "Swati Melkani",
             "2026-10-20",
             "Completed",
             now),
        ]
        cursor.executemany(
            """
            INSERT INTO quality_improvements (cycle_code, title, plan_problem, plan_objective, plan_action, do_implemented_change, do_linked_defect, check_retest_results, check_metrics_comparison, act_decision, act_lessons_learned, owner, target_date, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sample_pdca,
        )
    conn.commit()


def setup_database(db_path: Optional[str] = None) -> None:
    """Convenience bootstrap function to initialize schema and seed initial data.

    Args:
        db_path: Optional explicit database path.
    """
    from app.database.connection import create_connection
    conn = create_connection(db_path)
    try:
        init_db(conn)
        seed_default_settings(conn)
        seed_sample_menu(conn)
        seed_tqm_sample_data(conn)
    finally:
        conn.close()

"""Automated Tests for TQM Analytics: Checksheet, Pareto, FMEA, and PDCA.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management
"""

import sqlite3
from app.services.quality_service import (
    add_fmea_record,
    calculate_pareto_analysis,
    create_defect,
    get_defect_by_id,
    get_defects,
    get_fmea_records,
    get_quality_summary_metrics,
    update_defect_status,
)


def test_create_and_update_defect(db_conn: sqlite3.Connection):
    """Verify logging a defect and transitioning lifecycle status."""
    defect_id = create_defect(
        conn=db_conn,
        affected_module="Billing",
        description="Paisa rounding discrepancy under multiple line discounts",
        category="Calculation Error",
        severity="High",
        root_cause_category="Software Code",
        occurrence_count=5,
    )
    assert defect_id > 0

    defect = get_defect_by_id(db_conn, defect_id)
    assert defect["status"] == "Reported"
    assert defect["severity"] == "High"

    update_defect_status(
        conn=db_conn,
        defect_id=defect_id,
        new_status="Verified",
        corrective_action="Applied Decimal quantize ROUND_HALF_UP in billing_service.py",
    )
    updated = get_defect_by_id(db_conn, defect_id)
    assert updated["status"] == "Verified"
    assert "ROUND_HALF_UP" in updated["corrective_action"]


def test_fmea_rpn_calculation(db_conn: sqlite3.Connection):
    """Verify RPN = Severity x Occurrence x Detection calculation.

    S=8, O=4, D=3 -> RPN = 8 * 4 * 3 = 96
    """
    fmea_id = add_fmea_record(
        conn=db_conn,
        process_step="Invoice Finalization",
        potential_failure_mode="Duplicate invoice issued on double-click",
        potential_effect="Ledger inconsistency",
        potential_cause="Missing idempotency token",
        existing_controls="None",
        severity=8,
        occurrence=4,
        detection=3,
        recommended_mitigation="Database unique constraint with ACID transaction",
        responsible_role="Backend Developer",
    )
    assert fmea_id > 0

    records = get_fmea_records(db_conn)
    assert len(records) >= 1
    # Check that computed RPN equals 96
    rec = [r for r in records if r["id"] == fmea_id][0]
    assert rec["rpn"] == 96


def test_pareto_analysis_calculation(db_conn: sqlite3.Connection):
    """Verify Pareto cumulative frequency and percentage computations.

    Categories:
      CatA: 70 occurrences (70%)
      CatB: 20 occurrences (90% cumulative)
      CatC: 10 occurrences (100% cumulative)
    """
    create_defect(db_conn, "Module1", "Desc1", "CatA", "Medium", "Software Code", occurrence_count=70)
    create_defect(db_conn, "Module2", "Desc2", "CatB", "Medium", "Process", occurrence_count=20)
    create_defect(db_conn, "Module3", "Desc3", "CatC", "Low", "Testing", occurrence_count=10)

    pareto = calculate_pareto_analysis(db_conn)
    assert pareto["has_data"] is True
    assert pareto["labels"] == ["CatA", "CatB", "CatC"]
    assert pareto["counts"] == [70, 20, 10]
    assert pareto["cumulative_percentages"] == [70.0, 90.0, 100.0]
    assert "CatA" in pareto["vital_few"]


def test_empty_pareto_dataset_handling(db_conn: sqlite3.Connection):
    """Verify empty defect table returns graceful structure without crashing."""
    pareto = calculate_pareto_analysis(db_conn)
    assert pareto["has_data"] is False
    assert len(pareto["labels"]) == 0
    assert "No quality defect data recorded yet" in pareto["summary_text"]

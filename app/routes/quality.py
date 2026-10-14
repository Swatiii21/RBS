"""Total Quality Management (TQM) Quality Dashboard Route Handler.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides interactive tools demonstrating TQM principles:
1. Executive Quality Metrics Overview
2. Defect Checksheet & CSV Export
3. Pareto Analysis Chart & 80/20 Insights
4. Ishikawa (Fishbone) Diagram
5. Failure Mode and Effects Analysis (FMEA) Matrix
6. SIPOC Process Map
7. PDCA Continuous Improvement Register
"""

from __future__ import annotations

import csv
import io
from typing import Any
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from app.database.connection import get_db
from app.services.quality_service import (
    add_fmea_record,
    calculate_pareto_analysis,
    create_defect,
    get_defects,
    get_fishbone_causes,
    get_fmea_records,
    get_pdca_cycles,
    get_quality_summary_metrics,
    update_defect_status,
)

quality_bp = Blueprint("quality", __name__, url_prefix="/quality")


@quality_bp.route("/")
def index() -> str:
    """Render comprehensive TQM Quality Dashboard."""
    conn = get_db()
    summary = get_quality_summary_metrics(conn)
    pareto_data = calculate_pareto_analysis(conn)
    pdca_list = get_pdca_cycles(conn)
    return render_template(
        "quality/index.html",
        summary=summary,
        pareto_data=pareto_data,
        pdca_list=pdca_list,
    )


@quality_bp.route("/defects", methods=["GET", "POST"])
def defects() -> Any:
    """View and record defects on the Quality Checksheet."""
    conn = get_db()
    if request.method == "POST":
        affected_module = request.form.get("affected_module", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        severity = request.form.get("severity", "Medium")
        root_cause_category = request.form.get("root_cause_category", "").strip()
        occurrence_count = int(request.form.get("occurrence_count", 1))
        corrective_action = request.form.get("corrective_action", "").strip()

        try:
            create_defect(
                conn=conn,
                affected_module=affected_module,
                description=description,
                category=category,
                severity=severity,
                root_cause_category=root_cause_category,
                occurrence_count=occurrence_count,
                corrective_action=corrective_action or None,
                actor="QA Analyst",
            )
            flash("Quality defect successfully logged in checksheet.", "success")
            return redirect(url_for("quality.defects"))
        except ValueError as e:
            flash(str(e), "danger")

    status = request.args.get("status", "").strip()
    severity = request.args.get("severity", "").strip()
    search = request.args.get("search", "").strip()

    defects_list = get_defects(
        conn=conn,
        status=status or None,
        severity=severity or None,
        search=search or None,
    )
    return render_template(
        "quality/defects.html",
        defects=defects_list,
        current_status=status,
        current_severity=severity,
        current_search=search,
    )


@quality_bp.route("/defects/<int:defect_id>/status", methods=["POST"])
def defect_status(defect_id: int) -> Any:
    """Transition defect lifecycle status."""
    conn = get_db()
    new_status = request.form.get("status", "Reported")
    corrective_action = request.form.get("corrective_action", "").strip()

    try:
        update_defect_status(
            conn=conn,
            defect_id=defect_id,
            new_status=new_status,
            corrective_action=corrective_action or None,
            actor="QA Lead",
        )
        flash(f"Defect status updated to '{new_status}'.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("quality.defects"))


@quality_bp.route("/defects/export-csv")
def export_defects_csv() -> Response:
    """Export defect register to CSV file."""
    conn = get_db()
    defects_list = get_defects(conn)

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow([
        "Defect Code", "Date Reported", "Module", "Category", "Severity",
        "Occurrences", "Root Cause Category", "Status", "Resolution Date", "Description"
    ])

    for d in defects_list:
        writer.writerow([
            d["defect_code"], d["date_reported"], d["affected_module"], d["category"],
            d["severity"], d["occurrence_count"], d["root_cause_category"], d["status"],
            d["resolution_date"] or "N/A", d["description"]
        ])

    output = Response(si.getvalue(), mimetype="text/csv")
    output.headers["Content-Disposition"] = "attachment; filename=tqm_defects_register.csv"
    return output


@quality_bp.route("/pareto")
def pareto() -> str:
    """Display interactive Pareto chart and analysis."""
    conn = get_db()
    pareto_data = calculate_pareto_analysis(conn)
    return render_template("quality/pareto.html", pareto_data=pareto_data)


@quality_bp.route("/fmea", methods=["GET", "POST"])
def fmea() -> Any:
    """Display Failure Mode and Effects Analysis (FMEA) Matrix and calculate RPN."""
    conn = get_db()
    if request.method == "POST":
        step = request.form.get("process_step", "").strip()
        mode = request.form.get("potential_failure_mode", "").strip()
        effect = request.form.get("potential_effect", "").strip()
        cause = request.form.get("potential_cause", "").strip()
        controls = request.form.get("existing_controls", "").strip()
        sev = int(request.form.get("severity", 5))
        occ = int(request.form.get("occurrence", 5))
        det = int(request.form.get("detection", 5))
        mitigation = request.form.get("recommended_mitigation", "").strip()
        role = request.form.get("responsible_role", "Admin").strip()

        try:
            add_fmea_record(
                conn=conn,
                process_step=step,
                potential_failure_mode=mode,
                potential_effect=effect,
                potential_cause=cause,
                existing_controls=controls,
                severity=sev,
                occurrence=occ,
                detection=det,
                recommended_mitigation=mitigation,
                responsible_role=role,
            )
            flash(f"FMEA record added. RPN computed as {sev * occ * det}.", "success")
            return redirect(url_for("quality.fmea"))
        except ValueError as e:
            flash(str(e), "danger")

    fmea_records = get_fmea_records(conn)
    return render_template("quality/fmea.html", records=fmea_records)


@quality_bp.route("/fishbone")
def fishbone() -> str:
    """Display Ishikawa / Fishbone root-cause taxonomy."""
    causes = get_fishbone_causes()
    return render_template("quality/fishbone.html", causes=causes)


@quality_bp.route("/sipoc")
def sipoc() -> str:
    """Display SIPOC process map for restaurant billing."""
    return render_template("quality/sipoc.html")


@quality_bp.route("/pdca")
def pdca() -> str:
    """Display Continuous Improvement (PDCA) register with verified test evidence."""
    conn = get_db()
    cycles = get_pdca_cycles(conn)
    return render_template("quality/pdca.html", cycles=cycles)

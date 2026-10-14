"""Activity Logs Route Handler.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides administrative inspection of business audit events stored in SQLite.
Distinguishes between business audit logs (auditing critical user and data actions)
and technical diagnostic logs stored in the rotating file logs/app.log.
"""

from __future__ import annotations

from flask import Blueprint, render_template, request

from app.database.connection import get_db
from app.services.logging_service import get_activity_logs
from app.services.settings_service import get_setting

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")


@logs_bp.route("/")
def index() -> str:
    """Render filterable and paginated business audit logs."""
    conn = get_db()
    module = request.args.get("module", "").strip()
    outcome = request.args.get("outcome", "").strip()
    action_type = request.args.get("action_type", "").strip()
    search = request.args.get("search", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(get_setting(conn, "default_page_size", 15))

    logs, total = get_activity_logs(
        conn=conn,
        module=module or None,
        outcome=outcome or None,
        action_type=action_type or None,
        search=search or None,
        page=page,
        per_page=per_page,
    )
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "logs/index.html",
        logs=logs,
        total=total,
        page=page,
        total_pages=total_pages,
        current_module=module,
        current_outcome=outcome,
        current_action=action_type,
        current_search=search,
    )

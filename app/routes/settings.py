"""System Settings Route Handler.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides the administrative web interface for viewing and modifying persistent
application parameters (tax rate, currency, discount threshold, log policies, restaurant info)
without source code changes or application restarts.
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.database.connection import get_db
from app.services.settings_service import get_grouped_settings, update_settings_batch

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET", "POST"])
def index() -> Any:
    """Display and update grouped system settings."""
    conn = get_db()
    if request.method == "POST":
        # Extract all form fields that match system settings
        updates = {}
        for key, val in request.form.items():
            if key != "csrf_token":
                updates[key] = val

        try:
            changed_keys = update_settings_batch(
                conn=conn,
                updates=updates,
                updated_by="Administrator",
            )
            flash(
                f"Successfully updated {len(changed_keys)} system setting(s). Changes take effect immediately.",
                "success",
            )
            return redirect(url_for("settings.index"))
        except ValueError as e:
            flash(f"Validation Error: {str(e)}", "danger")

    grouped = get_grouped_settings(conn)
    return render_template("settings/index.html", grouped=grouped)

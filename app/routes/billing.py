"""Billing and Invoice Generation Route Handler.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Handles transactional invoice finalization, printable tax invoices, and
historical billing register searches.
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.database.connection import get_db
from app.services.billing_service import (
    finalize_order_and_generate_invoice,
    get_invoice_by_number,
    get_invoices_history,
)
from app.services.settings_service import get_setting

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.route("/finalize/<int:order_id>", methods=["POST"])
def finalize(order_id: int) -> Any:
    """Atomically finalize Draft order and generate an immutable invoice."""
    conn = get_db()
    notes = request.form.get("notes", "").strip()

    try:
        inv_data = finalize_order_and_generate_invoice(
            conn=conn,
            order_id=order_id,
            actor="Staff",
            notes=notes or None,
        )
        flash(f"Invoice {inv_data['invoice_number']} successfully finalized!", "success")
        return redirect(url_for("billing.view_invoice", invoice_number=inv_data["invoice_number"]))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("orders.detail", order_id=order_id))


@billing_bp.route("/invoice/<invoice_number>")
def view_invoice(invoice_number: str) -> Any:
    """Render print-ready official tax invoice."""
    conn = get_db()
    data = get_invoice_by_number(conn, invoice_number)
    if not data:
        flash(f"Invoice '{invoice_number}' not found.", "danger")
        return redirect(url_for("billing.history"))

    return render_template(
        "billing/invoice.html",
        invoice=data["invoice"],
        items=data["items"],
        footer_text=data["footer_text"],
        currency_symbol=data["currency_symbol"],
    )


@billing_bp.route("/history")
def history() -> str:
    """Display searchable, filterable, and paginated invoice ledger."""
    conn = get_db()
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(get_setting(conn, "default_page_size", 15))

    invoices, total = get_invoices_history(
        conn=conn,
        search=search or None,
        status=status or None,
        start_date=start_date or None,
        end_date=end_date or None,
        page=page,
        per_page=per_page,
    )
    currency_symbol = get_setting(conn, "currency_symbol", "₹")
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "billing/index.html",
        invoices=invoices,
        total=total,
        page=page,
        total_pages=total_pages,
        current_search=search,
        current_status=status,
        start_date=start_date,
        end_date=end_date,
        currency_symbol=currency_symbol,
    )

"""Dashboard Route Handler.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides aggregated operational statistics calculated dynamically from the SQLite database:
- Today's total sales volume
- Number of finalized bills
- Total catalog menu items
- Active open (draft) orders
- Historical sales summary for browser chart visualization
- Top popular items breakdown
- Quick action navigation links
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from flask import Blueprint, render_template

from app.database.connection import get_db
from app.services.settings_service import get_setting

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def index() -> str:
    """Render operational executive dashboard with live metrics."""
    conn = get_db()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Total sales today (sum of finalized invoices today)
    cursor.execute(
        "SELECT COALESCE(SUM(grand_total), 0.0) AS today_sales, COUNT(*) AS today_invoices "
        "FROM invoices WHERE DATE(invoice_date) = DATE(?) AND status = 'Active'",
        (today_str,),
    )
    today_row = cursor.fetchone()
    today_sales = float(today_row["today_sales"])
    today_invoices = int(today_row["today_invoices"])

    # 2. Total active menu items
    cursor.execute("SELECT COUNT(*) AS total_menu FROM menu_items WHERE is_available = 1")
    total_menu = int(cursor.fetchone()["total_menu"])

    # 3. Active draft orders
    cursor.execute("SELECT COUNT(*) AS pending_orders FROM orders WHERE status = 'Draft'")
    pending_orders = int(cursor.fetchone()["pending_orders"])

    # 4. Recent billing activity (latest 5 finalized invoices)
    cursor.execute(
        """
        SELECT i.invoice_number, i.invoice_date, i.grand_total, o.customer_name, o.table_number, o.order_type
        FROM invoices i
        JOIN orders o ON i.order_id = o.id
        ORDER BY i.id DESC
        LIMIT 5
        """
    )
    recent_invoices = cursor.fetchall()

    # 5. Last 7 days sales data for Chart.js
    cursor.execute(
        """
        SELECT DATE(invoice_date) AS sale_date, SUM(grand_total) AS daily_total, COUNT(*) AS count
        FROM invoices
        WHERE status = 'Active'
        GROUP BY DATE(invoice_date)
        ORDER BY DATE(invoice_date) DESC
        LIMIT 7
        """
    )
    sales_trend_rows = list(reversed(cursor.fetchall()))
    chart_dates = [r["sale_date"] for r in sales_trend_rows]
    chart_sales = [float(r["daily_total"]) for r in sales_trend_rows]

    # Fallback chart data if empty database
    if not chart_dates:
        chart_dates = [today_str]
        chart_sales = [0.0]

    # 6. Top ordered items
    cursor.execute(
        """
        SELECT item_name, SUM(quantity) AS total_qty
        FROM order_items
        GROUP BY item_name
        ORDER BY total_qty DESC
        LIMIT 5
        """
    )
    top_items_rows = cursor.fetchall()
    top_item_labels = [r["item_name"] for r in top_items_rows]
    top_item_counts = [int(r["total_qty"]) for r in top_items_rows]

    # 7. Quality indicator count
    cursor.execute("SELECT COUNT(*) AS open_defects FROM quality_defects WHERE status IN ('Reported', 'Investigating')")
    open_defects = int(cursor.fetchone()["open_defects"])

    currency_symbol = get_setting(conn, "currency_symbol", "₹")

    return render_template(
        "dashboard.html",
        today_sales=today_sales,
        today_invoices=today_invoices,
        total_menu=total_menu,
        pending_orders=pending_orders,
        recent_invoices=recent_invoices,
        chart_dates=chart_dates,
        chart_sales=chart_sales,
        top_item_labels=top_item_labels,
        top_item_counts=top_item_counts,
        open_defects=open_defects,
        currency_symbol=currency_symbol,
    )

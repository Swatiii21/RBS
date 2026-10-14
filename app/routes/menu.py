"""Menu Management Route Handler.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Handles HTTP requests for Menu CRUD operations, input validation, and user feedback.
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.database.connection import get_db
from app.services.menu_service import (
    create_menu_item,
    deactivate_menu_item,
    delete_menu_item,
    get_categories,
    get_menu_item_by_id,
    get_menu_items,
    update_menu_item,
)
from app.services.settings_service import get_setting

menu_bp = Blueprint("menu", __name__, url_prefix="/menu")


@menu_bp.route("/")
def index() -> str:
    """Display searchable, filterable menu catalog."""
    conn = get_db()
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(get_setting(conn, "default_page_size", 15))

    items, total = get_menu_items(
        conn=conn,
        search=search or None,
        category=category or None,
        page=page,
        per_page=per_page,
    )
    categories = get_categories(conn)
    currency_symbol = get_setting(conn, "currency_symbol", "₹")

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "menu/index.html",
        items=items,
        total=total,
        page=page,
        total_pages=total_pages,
        categories=categories,
        current_search=search,
        current_category=category,
        currency_symbol=currency_symbol,
    )


@menu_bp.route("/create", methods=["GET", "POST"])
def create() -> Any:
    """Create a new menu item."""
    conn = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        unit_price = request.form.get("unit_price", "0")
        description = request.form.get("description", "").strip()
        item_code = request.form.get("item_code", "").strip()
        is_available = 1 if request.form.get("is_available") == "1" else 0

        try:
            create_menu_item(
                conn=conn,
                name=name,
                category=category,
                unit_price=unit_price,
                description=description,
                item_code=item_code or None,
                is_available=is_available,
                actor="Staff",
            )
            flash(f"Menu item '{name}' was successfully added.", "success")
            return redirect(url_for("menu.index"))
        except ValueError as e:
            flash(str(e), "danger")

    categories = get_categories(conn)
    return render_template("menu/form.html", item=None, categories=categories, is_edit=False)


@menu_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
def edit(item_id: int) -> Any:
    """Edit existing menu item."""
    conn = get_db()
    item = get_menu_item_by_id(conn, item_id)
    if not item:
        flash(f"Menu item #{item_id} not found.", "danger")
        return redirect(url_for("menu.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        unit_price = request.form.get("unit_price", "0")
        description = request.form.get("description", "").strip()
        is_available = 1 if request.form.get("is_available") == "1" else 0

        try:
            update_menu_item(
                conn=conn,
                item_id=item_id,
                name=name,
                category=category,
                unit_price=unit_price,
                description=description,
                is_available=is_available,
                actor="Staff",
            )
            flash(f"Menu item '{name}' has been updated.", "success")
            return redirect(url_for("menu.index"))
        except ValueError as e:
            flash(str(e), "danger")

    categories = get_categories(conn)
    return render_template("menu/form.html", item=item, categories=categories, is_edit=True)


@menu_bp.route("/<int:item_id>/toggle", methods=["POST"])
def toggle(item_id: int) -> Any:
    """Toggle availability status of menu item."""
    conn = get_db()
    item = get_menu_item_by_id(conn, item_id)
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for("menu.index"))

    new_status = 0 if item["is_available"] else 1
    now_desc = "Available" if new_status else "Unavailable"
    cursor = conn.cursor()
    cursor.execute("UPDATE menu_items SET is_available = ? WHERE id = ?", (new_status, item_id))
    conn.commit()

    flash(f"Item '{item['name']}' is now marked {now_desc}.", "info")
    return redirect(url_for("menu.index"))


@menu_bp.route("/<int:item_id>/delete", methods=["POST"])
def delete(item_id: int) -> Any:
    """Safely delete menu item if not referenced in historical receipts."""
    conn = get_db()
    try:
        delete_menu_item(conn, item_id, actor="Staff")
        flash("Menu item was permanently removed.", "success")
    except ValueError as e:
        flash(str(e), "warning")

    return redirect(url_for("menu.index"))

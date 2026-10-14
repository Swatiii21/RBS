"""Order Management Route Handler.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Handles active orders, cart item additions, quantity modifications, discounts,
and order cancellation with live recalculation.
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.database.connection import get_db
from app.services.menu_service import get_menu_items
from app.services.order_service import (
    add_item_to_order,
    cancel_order,
    create_order,
    get_order_by_id,
    get_order_items,
    get_orders,
    remove_order_item,
    update_order_discount,
    update_order_item_quantity,
)
from app.services.settings_service import get_setting

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("/")
def index() -> str:
    """Display list of orders filtered by status or search keyword."""
    conn = get_db()
    status = request.args.get("status", "").strip()
    order_type = request.args.get("order_type", "").strip()
    search = request.args.get("search", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(get_setting(conn, "default_page_size", 15))

    orders_list, total = get_orders(
        conn=conn,
        status=status or None,
        order_type=order_type or None,
        search=search or None,
        page=page,
        per_page=per_page,
    )
    currency_symbol = get_setting(conn, "currency_symbol", "₹")
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "orders/index.html",
        orders=orders_list,
        total=total,
        page=page,
        total_pages=total_pages,
        current_status=status,
        current_type=order_type,
        current_search=search,
        currency_symbol=currency_symbol,
    )


@orders_bp.route("/create", methods=["GET", "POST"])
def create() -> Any:
    """Initialize a new Draft order."""
    conn = get_db()
    if request.method == "POST":
        order_type = request.form.get("order_type", "Dine-in")
        table_number = request.form.get("table_number", "").strip()
        customer_name = request.form.get("customer_name", "").strip()
        customer_contact = request.form.get("customer_contact", "").strip()
        discount_rate = float(request.form.get("discount_rate", 0.0) or 0.0)

        try:
            order_id = create_order(
                conn=conn,
                order_type=order_type,
                table_number=table_number,
                customer_name=customer_name,
                customer_contact=customer_contact,
                discount_rate=discount_rate,
                actor="Staff",
            )
            flash("New order created. Please add items.", "success")
            return redirect(url_for("orders.detail", order_id=order_id))
        except ValueError as e:
            flash(str(e), "danger")

    max_discount = get_setting(conn, "max_discount_percentage", 25.0)
    return render_template("orders/create.html", max_discount=max_discount)


@orders_bp.route("/<int:order_id>")
def detail(order_id: int) -> Any:
    """Detailed interactive order workstation for adding items and calculating bill."""
    conn = get_db()
    order = get_order_by_id(conn, order_id)
    if not order:
        flash(f"Order #{order_id} not found.", "danger")
        return redirect(url_for("orders.index"))

    items = get_order_items(conn, order_id)
    # Available menu items to select from
    available_menu, _ = get_menu_items(conn, available_only=True, per_page=100)
    currency_symbol = get_setting(conn, "currency_symbol", "₹")
    max_discount = float(get_setting(conn, "max_discount_percentage", 25.0))

    return render_template(
        "orders/detail.html",
        order=order,
        items=items,
        available_menu=available_menu,
        currency_symbol=currency_symbol,
        max_discount=max_discount,
    )


@orders_bp.route("/<int:order_id>/add-item", methods=["POST"])
def add_item(order_id: int) -> Any:
    """Add selected menu item to active order."""
    conn = get_db()
    menu_item_id = int(request.form.get("menu_item_id", 0))
    quantity = int(request.form.get("quantity", 1))

    try:
        add_item_to_order(conn, order_id, menu_item_id, quantity, actor="Staff")
        flash("Item added to order.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("orders.detail", order_id=order_id))


@orders_bp.route("/<int:order_id>/item/<int:order_item_id>/update", methods=["POST"])
def update_item_qty(order_id: int, order_item_id: int) -> Any:
    """Update item quantity or remove if zero."""
    conn = get_db()
    new_quantity = int(request.form.get("quantity", 1))

    try:
        update_order_item_quantity(conn, order_id, order_item_id, new_quantity, actor="Staff")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("orders.detail", order_id=order_id))


@orders_bp.route("/<int:order_id>/item/<int:order_item_id>/delete", methods=["POST"])
def delete_item(order_id: int, order_item_id: int) -> Any:
    """Remove line item from order."""
    conn = get_db()
    try:
        remove_order_item(conn, order_id, order_item_id, actor="Staff")
        flash("Item removed from bill.", "info")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("orders.detail", order_id=order_id))


@orders_bp.route("/<int:order_id>/discount", methods=["POST"])
def update_discount(order_id: int) -> Any:
    """Update order discount percentage."""
    conn = get_db()
    try:
        discount_rate = float(request.form.get("discount_rate", 0.0))
        update_order_discount(conn, order_id, discount_rate, actor="Staff")
        flash(f"Discount updated to {discount_rate}%.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("orders.detail", order_id=order_id))


@orders_bp.route("/<int:order_id>/cancel", methods=["POST"])
def cancel(order_id: int) -> Any:
    """Cancel order."""
    conn = get_db()
    reason = request.form.get("reason", "").strip()
    try:
        cancel_order(conn, order_id, reason=reason, actor="Staff")
        flash("Order has been cancelled.", "warning")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("orders.index"))

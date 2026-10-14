"""Order Management Service.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides:
- Order lifecycle management (Draft -> Finalized / Cancelled).
- Item snapshot pricing: menu item name and price are captured at time of order,
  preventing retrospective tampering of past bills when menu prices fluctuate.
- Dynamic server-side recalculation of line totals, subtotal, discount, tax, and grand total.
- Strict rejection of negative quantities, unavailable menu items, and invalid discounts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import sqlite3

from app.database.connection import transaction
from app.services.billing_service import calculate_billing_breakdown
from app.services.logging_service import log_activity
from app.services.menu_service import get_menu_item_by_id
from app.services.settings_service import get_setting


def generate_order_number(conn: sqlite3.Connection) -> str:
    """Generate the next unique sequential order number (e.g. ORD-2026-0001).

    Args:
        conn: SQLite connection.

    Returns:
        str: Unique order identifier.
    """
    year = datetime.now().year
    prefix = f"ORD-{year}-"
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_number FROM orders WHERE order_number LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",),
    )
    row = cursor.fetchone()
    if row:
        last_num = row["order_number"].replace(prefix, "")
        try:
            seq = int(last_num) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def get_orders(
    conn: sqlite3.Connection,
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 15,
) -> Tuple[List[sqlite3.Row], int]:
    """Retrieve filtered and paginated list of orders.

    Args:
        conn: SQLite connection.
        status: Filter by status ('Draft', 'Finalized', 'Cancelled').
        order_type: Filter by 'Dine-in' or 'Takeaway'.
        search: Filter by order number, customer name, or table number.
        page: Page index (1-indexed).
        per_page: Items per page.

    Returns:
        Tuple[List[sqlite3.Row], int]: Matched orders and total count.
    """
    conditions = []
    params: List[Any] = []

    if status:
        conditions.append("status = ?")
        params.append(status)

    if order_type:
        conditions.append("order_type = ?")
        params.append(order_type)

    if search:
        conditions.append("(order_number LIKE ? OR customer_name LIKE ? OR table_number LIKE ?)")
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) AS total FROM orders{where_clause}", params)
    total_count = cursor.fetchone()["total"]

    offset = max(0, (page - 1) * per_page)
    cursor.execute(
        f"""
        SELECT * FROM orders{where_clause}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        params + [per_page, offset],
    )
    rows = cursor.fetchall()
    return rows, total_count


def get_order_by_id(conn: sqlite3.Connection, order_id: int) -> Optional[sqlite3.Row]:
    """Retrieve a single order row by primary key.

    Args:
        conn: SQLite connection.
        order_id: Order primary key.

    Returns:
        Optional[sqlite3.Row]: Order row or None.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    return cursor.fetchone()


def get_order_items(conn: sqlite3.Connection, order_id: int) -> List[sqlite3.Row]:
    """Retrieve line items associated with an order.

    Args:
        conn: SQLite connection.
        order_id: Order primary key.

    Returns:
        List[sqlite3.Row]: Line items ordered by ID.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC", (order_id,))
    return cursor.fetchall()


def recalculate_order_totals(conn: sqlite3.Connection, order_id: int) -> Dict[str, float]:
    """Recalculate order financial figures from line items using server-enforced Decimal rules.

    Args:
        conn: SQLite connection.
        order_id: Order primary key.

    Returns:
        Dict[str, float]: Updated billing breakdown dictionary.
    """
    order = get_order_by_id(conn, order_id)
    if not order:
        raise ValueError(f"Order #{order_id} not found.")

    items = get_order_items(conn, order_id)
    items_data = [{"quantity": item["quantity"], "unit_price": item["unit_price"]} for item in items]

    max_disc = float(get_setting(conn, "max_discount_percentage", 25.0))
    rounding_policy = get_setting(conn, "rounding_policy", "ROUND_HALF_UP")

    calc = calculate_billing_breakdown(
        items=items_data,
        discount_rate=order["discount_rate"],
        tax_rate=order["tax_rate"],
        max_discount_limit=max_disc,
        rounding_policy=rounding_policy,
    )

    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE orders
        SET subtotal = ?, discount_amount = ?, taxable_amount = ?,
            tax_amount = ?, grand_total = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            float(calc.subtotal),
            float(calc.discount_amount),
            float(calc.taxable_amount),
            float(calc.tax_amount),
            float(calc.grand_total),
            now,
            order_id,
        ),
    )
    conn.commit()
    return calc.to_dict()


def create_order(
    conn: sqlite3.Connection,
    order_type: str,
    table_number: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_contact: Optional[str] = None,
    discount_rate: float = 0.0,
    actor: str = "Staff",
) -> int:
    """Create a new Draft order.

    Args:
        conn: SQLite connection.
        order_type: 'Dine-in' or 'Takeaway'.
        table_number: Optional table designation.
        customer_name: Optional customer name.
        customer_contact: Optional customer phone.
        discount_rate: Initial promotional discount rate.
        actor: Operator creating the order.

    Returns:
        int: Primary key ID of created order.

    Raises:
        ValueError: If parameters are invalid.
    """
    if order_type not in ("Dine-in", "Takeaway"):
        raise ValueError("Order type must be either 'Dine-in' or 'Takeaway'.")

    # Enforce table number for Dine-in
    clean_table = table_number.strip() if table_number else ""
    if order_type == "Dine-in" and not clean_table:
        clean_table = "T-1"  # Default table if unspecified

    max_disc = float(get_setting(conn, "max_discount_percentage", 25.0))
    tax_rate = float(get_setting(conn, "default_tax_rate", 5.0))

    if discount_rate < 0.0 or discount_rate > max_disc:
        raise ValueError(f"Discount rate must be between 0% and {max_disc}%.")

    order_num = generate_order_number(conn)
    now = datetime.now(timezone.utc).isoformat()

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orders (
            order_number, order_type, table_number, customer_name, customer_contact,
            status, subtotal, discount_rate, discount_amount, taxable_amount,
            tax_rate, tax_amount, grand_total, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'Draft', 0.0, ?, 0.0, 0.0, ?, 0.0, 0.0, ?, ?)
        """,
        (
            order_num,
            order_type,
            clean_table or None,
            customer_name.strip() if customer_name else None,
            customer_contact.strip() if customer_contact else None,
            discount_rate,
            tax_rate,
            now,
            now,
        ),
    )
    conn.commit()
    order_id = cursor.lastrowid

    log_activity(
        conn=conn,
        action_type="ORDER_CREATE",
        module="Orders",
        description=f"Created new {order_type} order {order_num} for table '{clean_table}'",
        actor=actor,
        affected_record_id=order_num,
        outcome="Success",
    )
    return order_id


def add_item_to_order(
    conn: sqlite3.Connection,
    order_id: int,
    menu_item_id: int,
    quantity: int = 1,
    actor: str = "Staff",
) -> None:
    """Add a menu item to an active Draft order or increase its existing quantity.

    Args:
        conn: SQLite connection.
        order_id: Target order ID.
        menu_item_id: Menu item to add.
        quantity: Positive quantity.
        actor: Operator.

    Raises:
        ValueError: If order is finalized/cancelled, item is unavailable, or quantity <= 0.
    """
    order = get_order_by_id(conn, order_id)
    if not order:
        raise ValueError(f"Order #{order_id} not found.")

    if order["status"] != "Draft":
        raise ValueError(f"Cannot modify order #{order['order_number']}: status is '{order['status']}'.")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    menu_item = get_menu_item_by_id(conn, menu_item_id)
    if not menu_item:
        raise ValueError(f"Menu item #{menu_item_id} not found.")

    if not menu_item["is_available"]:
        raise ValueError(f"Menu item '{menu_item['name']}' is currently marked unavailable.")

    # Check if this item is already present in this order
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, quantity, unit_price FROM order_items WHERE order_id = ? AND menu_item_id = ?",
        (order_id, menu_item_id),
    )
    existing = cursor.fetchone()
    now = datetime.now(timezone.utc).isoformat()

    if existing:
        new_qty = existing["quantity"] + quantity
        line_total = round(new_qty * existing["unit_price"], 2)
        cursor.execute(
            "UPDATE order_items SET quantity = ?, line_total = ? WHERE id = ?",
            (new_qty, line_total, existing["id"]),
        )
    else:
        # Snapshot current unit price and item name
        unit_price = menu_item["unit_price"]
        line_total = round(quantity * unit_price, 2)
        cursor.execute(
            """
            INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (order_id, menu_item_id, menu_item["name"], unit_price, quantity, line_total, now),
        )

    conn.commit()
    recalculate_order_totals(conn, order_id)

    log_activity(
        conn=conn,
        action_type="ORDER_ITEM_ADD",
        module="Orders",
        description=f"Added {quantity}x '{menu_item['name']}' to order #{order['order_number']}",
        actor=actor,
        affected_record_id=order["order_number"],
        outcome="Success",
    )


def update_order_item_quantity(
    conn: sqlite3.Connection,
    order_id: int,
    order_item_id: int,
    new_quantity: int,
    actor: str = "Staff",
) -> None:
    """Adjust the quantity of an item in a Draft order. Removes item if quantity reaches zero.

    Args:
        conn: SQLite connection.
        order_id: Order primary key.
        order_item_id: Line item primary key.
        new_quantity: New quantity (>= 0).
        actor: Operator.

    Raises:
        ValueError: If order is finalized or item not found.
    """
    order = get_order_by_id(conn, order_id)
    if not order or order["status"] != "Draft":
        raise ValueError("Cannot edit items in non-draft order.")

    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, item_name, unit_price FROM order_items WHERE id = ? AND order_id = ?",
        (order_item_id, order_id),
    )
    item = cursor.fetchone()
    if not item:
        raise ValueError(f"Line item #{order_item_id} not found in this order.")

    if new_quantity <= 0:
        cursor.execute("DELETE FROM order_items WHERE id = ?", (order_item_id,))
        log_desc = f"Removed item '{item['item_name']}' from order #{order['order_number']}"
    else:
        line_total = round(new_quantity * item["unit_price"], 2)
        cursor.execute(
            "UPDATE order_items SET quantity = ?, line_total = ? WHERE id = ?",
            (new_quantity, line_total, order_item_id),
        )
        log_desc = f"Updated '{item['item_name']}' quantity to {new_quantity} in order #{order['order_number']}"

    conn.commit()
    recalculate_order_totals(conn, order_id)

    log_activity(
        conn=conn,
        action_type="ORDER_ITEM_UPDATE",
        module="Orders",
        description=log_desc,
        actor=actor,
        affected_record_id=order["order_number"],
        outcome="Success",
    )


def remove_order_item(
    conn: sqlite3.Connection,
    order_id: int,
    order_item_id: int,
    actor: str = "Staff",
) -> None:
    """Remove a line item completely from a Draft order.

    Args:
        conn: SQLite connection.
        order_id: Order primary key.
        order_item_id: Line item primary key.
        actor: Operator.
    """
    update_order_item_quantity(conn, order_id, order_item_id, new_quantity=0, actor=actor)


def update_order_discount(
    conn: sqlite3.Connection,
    order_id: int,
    discount_rate: float,
    actor: str = "Staff",
) -> None:
    """Update promotional discount percentage on a Draft order with server-enforced boundary checks.

    Args:
        conn: SQLite connection.
        order_id: Order primary key.
        discount_rate: Discount percentage.
        actor: Operator.

    Raises:
        ValueError: If discount exceeds configured maximum or order is not Draft.
    """
    order = get_order_by_id(conn, order_id)
    if not order or order["status"] != "Draft":
        raise ValueError("Cannot modify discount on non-draft order.")

    max_disc = float(get_setting(conn, "max_discount_percentage", 25.0))
    if discount_rate < 0.0 or discount_rate > max_disc:
        raise ValueError(
            f"Discount rate {discount_rate}% is invalid. Must be between 0% and {max_disc}%."
        )

    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET discount_rate = ? WHERE id = ?",
        (discount_rate, order_id),
    )
    conn.commit()
    recalculate_order_totals(conn, order_id)

    log_activity(
        conn=conn,
        action_type="ORDER_DISCOUNT_UPDATE",
        module="Orders",
        description=f"Applied {discount_rate}% discount to order #{order['order_number']}",
        actor=actor,
        affected_record_id=order["order_number"],
        outcome="Success",
    )


def cancel_order(
    conn: sqlite3.Connection,
    order_id: int,
    reason: Optional[str] = None,
    actor: str = "Staff",
) -> None:
    """Cancel a Draft order.

    Args:
        conn: SQLite connection.
        order_id: Order primary key.
        reason: Optional cancellation rationale.
        actor: Operator.

    Raises:
        ValueError: If order is already Finalized.
    """
    order = get_order_by_id(conn, order_id)
    if not order:
        raise ValueError(f"Order #{order_id} not found.")

    if order["status"] == "Finalized":
        raise ValueError(
            f"Cannot cancel Order #{order['order_number']}: it is already Finalized and invoiced. "
            f"Use formal correction procedure."
        )

    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = 'Cancelled', updated_at = ? WHERE id = ?",
        (now, order_id),
    )
    conn.commit()

    log_activity(
        conn=conn,
        action_type="ORDER_CANCEL",
        module="Orders",
        description=f"Cancelled order #{order['order_number']}. Reason: {reason or 'No reason provided'}",
        actor=actor,
        affected_record_id=order["order_number"],
        outcome="Warning",
    )

"""Automated Tests for Order Lifecycle and Cart Management.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management
"""

import pytest
import sqlite3

from app.services.menu_service import create_menu_item
from app.services.order_service import (
    add_item_to_order,
    cancel_order,
    create_order,
    get_order_by_id,
    get_order_items,
    remove_order_item,
    update_order_discount,
    update_order_item_quantity,
)
from app.services.billing_service import finalize_order_and_generate_invoice


def test_create_order_lifecycle(db_conn: sqlite3.Connection):
    """Test creating Draft order and adding dishes."""
    dish_id = create_menu_item(db_conn, "Veg Biryani", "Rice", 180.00)
    order_id = create_order(db_conn, "Dine-in", table_number="T-5", customer_name="Ramesh Kumar")

    order = get_order_by_id(db_conn, order_id)
    assert order["status"] == "Draft"
    assert order["table_number"] == "T-5"

    add_item_to_order(db_conn, order_id, dish_id, quantity=2)
    items = get_order_items(db_conn, order_id)
    assert len(items) == 1
    assert items[0]["quantity"] == 2
    assert items[0]["line_total"] == 360.00

    order_updated = get_order_by_id(db_conn, order_id)
    assert order_updated["subtotal"] == 360.00


def test_update_quantity_and_remove_item(db_conn: sqlite3.Connection):
    """Verify modifying quantity updates line total and subtotal."""
    dish_id = create_menu_item(db_conn, "Sweet Lassi", "Beverages", 70.00)
    order_id = create_order(db_conn, "Takeaway")
    add_item_to_order(db_conn, order_id, dish_id, quantity=3)

    item = get_order_items(db_conn, order_id)[0]
    update_order_item_quantity(db_conn, order_id, item["id"], new_quantity=5)

    order = get_order_by_id(db_conn, order_id)
    assert order["subtotal"] == 350.00

    # Remove item
    remove_order_item(db_conn, order_id, item["id"])
    assert len(get_order_items(db_conn, order_id)) == 0
    order_empty = get_order_by_id(db_conn, order_id)
    assert order_empty["subtotal"] == 0.00


def test_prevent_editing_finalized_order(db_conn: sqlite3.Connection):
    """Verify finalized orders cannot accept new items or edits."""
    dish_id = create_menu_item(db_conn, "Gulab Jamun", "Desserts", 80.00)
    order_id = create_order(db_conn, "Takeaway")
    add_item_to_order(db_conn, order_id, dish_id, quantity=1)

    finalize_order_and_generate_invoice(db_conn, order_id)

    with pytest.raises(ValueError, match="status is 'Finalized'"):
        add_item_to_order(db_conn, order_id, dish_id, quantity=1)


def test_cancel_order_workflow(db_conn: sqlite3.Connection):
    """Verify cancelling an open Draft order."""
    order_id = create_order(db_conn, "Dine-in", table_number="T-9")
    cancel_order(db_conn, order_id, reason="Customer departed before ordering")

    order = get_order_by_id(db_conn, order_id)
    assert order["status"] == "Cancelled"

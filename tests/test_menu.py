"""Automated Tests for Menu Management Service.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management
"""

import pytest
import sqlite3

from app.services.menu_service import (
    create_menu_item,
    deactivate_menu_item,
    delete_menu_item,
    get_menu_item_by_id,
    get_menu_items,
    update_menu_item,
)


def test_create_valid_menu_item(db_conn: sqlite3.Connection):
    """Verify adding a valid menu item succeeds and assigns unique item code."""
    item_id = create_menu_item(
        conn=db_conn,
        name="Paneer Lababdar",
        category="Main Course",
        unit_price=260.00,
        description="Fresh cottage cheese in creamy tomato sauce",
    )
    assert item_id > 0
    item = get_menu_item_by_id(db_conn, item_id)
    assert item is not None
    assert item["name"] == "Paneer Lababdar"
    assert item["unit_price"] == 260.00
    assert item["is_available"] == 1


def test_reject_negative_price(db_conn: sqlite3.Connection):
    """Server-side boundary check: negative prices must raise ValueError."""
    with pytest.raises(ValueError, match="cannot be negative"):
        create_menu_item(
            conn=db_conn,
            name="Free Soup",
            category="Starters",
            unit_price=-50.00,
        )


def test_prevent_duplicate_menu_item(db_conn: sqlite3.Connection):
    """Ensure duplicate items in the same category are blocked."""
    create_menu_item(
        conn=db_conn,
        name="Garlic Naan",
        category="Breads",
        unit_price=50.00,
    )
    with pytest.raises(ValueError, match="already exists"):
        create_menu_item(
            conn=db_conn,
            name="Garlic Naan",
            category="Breads",
            unit_price=55.00,
        )


def test_update_existing_menu_item(db_conn: sqlite3.Connection):
    """Verify modifying price and description updates properly."""
    item_id = create_menu_item(
        conn=db_conn,
        name="Masala Papad",
        category="Starters",
        unit_price=40.00,
    )
    update_menu_item(
        conn=db_conn,
        item_id=item_id,
        name="Crispy Masala Papad",
        category="Starters",
        unit_price=45.00,
        description="Topped with spiced onions and tomatoes",
        is_available=1,
    )
    item = get_menu_item_by_id(db_conn, item_id)
    assert item["name"] == "Crispy Masala Papad"
    assert item["unit_price"] == 45.00


def test_deactivate_menu_item(db_conn: sqlite3.Connection):
    """Verify deactivation sets is_available to 0."""
    item_id = create_menu_item(
        conn=db_conn,
        name="Seasonal Mango Shake",
        category="Beverages",
        unit_price=90.00,
    )
    deactivate_menu_item(db_conn, item_id)
    item = get_menu_item_by_id(db_conn, item_id)
    assert item["is_available"] == 0


def test_safe_delete_blocks_ordered_items(db_conn: sqlite3.Connection):
    """Ensure dishes with historical order links cannot be deleted."""
    item_id = create_menu_item(
        conn=db_conn,
        name="Jeera Rice",
        category="Rice",
        unit_price=120.00,
    )
    # Simulate an order item reference in database
    db_conn.execute(
        """
        INSERT INTO orders (order_number, order_type, created_at, updated_at)
        VALUES ('ORD-TEST-01', 'Dine-in', '2026-10-14T00:00:00', '2026-10-14T00:00:00')
        """
    )
    order_id = db_conn.execute("SELECT id FROM orders WHERE order_number = 'ORD-TEST-01'").fetchone()[0]
    db_conn.execute(
        """
        INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total, created_at)
        VALUES (?, ?, 'Jeera Rice', 120.0, 1, 120.0, '2026-10-14T00:00:00')
        """,
        (order_id, item_id),
    )
    db_conn.commit()

    with pytest.raises(ValueError, match="historical order records"):
        delete_menu_item(db_conn, item_id)

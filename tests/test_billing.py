"""Automated Tests for Billing Calculations, Decimal Precision, and ACID Invoicing.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management
"""

from decimal import Decimal
import pytest
import sqlite3

from app.services.billing_service import (
    calculate_billing_breakdown,
    finalize_order_and_generate_invoice,
    get_invoice_by_number,
)
from app.services.order_service import add_item_to_order, create_order
from app.services.menu_service import create_menu_item, update_menu_item


def test_billing_calculation_accuracy():
    """Verify subtotal, discount, taxable amount, tax, and grand total calculations.

    Items:
      2 x 250.00 = 500.00
      1 x 100.00 = 100.00
      Subtotal = 600.00
    Discount (10%):
      600.00 * 0.10 = 60.00
    Taxable Amount:
      600.00 - 60.00 = 540.00
    Tax (5%):
      540.00 * 0.05 = 27.00
    Grand Total:
      540.00 + 27.00 = 567.00
    """
    items = [
        {"quantity": 2, "unit_price": 250.00},
        {"quantity": 1, "unit_price": 100.00},
    ]
    calc = calculate_billing_breakdown(
        items=items,
        discount_rate=10.0,
        tax_rate=5.0,
        max_discount_limit=25.0,
    )

    assert calc.subtotal == Decimal("600.00")
    assert calc.discount_amount == Decimal("60.00")
    assert calc.taxable_amount == Decimal("540.00")
    assert calc.tax_amount == Decimal("27.00")
    assert calc.grand_total == Decimal("567.00")


def test_monetary_rounding_policy():
    """Verify consistent ROUND_HALF_UP behavior on fractional paise.

    Subtotal = 1 x 105.55 = 105.55
    Discount (10%): 10.555 -> 10.56
    Taxable: 105.55 - 10.56 = 94.99
    Tax (5%): 94.99 * 0.05 = 4.7495 -> 4.75
    Grand Total: 94.99 + 4.75 = 99.74
    """
    items = [{"quantity": 1, "unit_price": 105.55}]
    calc = calculate_billing_breakdown(
        items=items,
        discount_rate=10.0,
        tax_rate=5.0,
        rounding_policy="ROUND_HALF_UP",
    )
    assert calc.discount_amount == Decimal("10.56")
    assert calc.tax_amount == Decimal("4.75")
    assert calc.grand_total == Decimal("99.74")


def test_reject_discount_exceeding_configured_maximum():
    """Server-side boundary check: discount exceeding configured limit must raise ValueError."""
    items = [{"quantity": 1, "unit_price": 100.00}]
    with pytest.raises(ValueError, match="exceeds configured maximum"):
        calculate_billing_breakdown(
            items=items,
            discount_rate=30.0,  # 30% > 25% max limit
            tax_rate=5.0,
            max_discount_limit=25.0,
        )


def test_reject_negative_quantity_in_billing():
    """Reject quantity <= 0."""
    items = [{"quantity": -2, "unit_price": 100.00}]
    with pytest.raises(ValueError, match="greater than zero"):
        calculate_billing_breakdown(
            items=items,
            discount_rate=0.0,
            tax_rate=5.0,
        )


def test_preserve_historical_price_after_menu_change(db_conn: sqlite3.Connection):
    """Critical TQM feature: editing menu dish price later must NOT change past finalized bill."""
    menu_id = create_menu_item(db_conn, "Paneer Tikka", "Starters", 200.00)
    order_id = create_order(db_conn, "Dine-in", table_number="T-1")
    add_item_to_order(db_conn, order_id, menu_id, quantity=2)

    # Finalize bill at price 200 (Subtotal 400.00)
    inv = finalize_order_and_generate_invoice(db_conn, order_id)
    inv_data_before = get_invoice_by_number(db_conn, inv["invoice_number"])
    assert inv_data_before["invoice"]["subtotal"] == 400.00

    # Now update menu price from 200.00 to 350.00
    update_menu_item(db_conn, menu_id, "Paneer Tikka", "Starters", 350.00)

    # Re-fetch invoice and ensure it STILL has subtotal 400.00
    inv_data_after = get_invoice_by_number(db_conn, inv["invoice_number"])
    assert inv_data_after["invoice"]["subtotal"] == 400.00
    assert inv_data_after["items"][0]["unit_price"] == 200.00


def test_rollback_on_failed_finalization(db_conn: sqlite3.Connection):
    """Ensure ACID transaction: cannot finalize empty order; order remains in Draft state."""
    order_id = create_order(db_conn, "Takeaway")
    with pytest.raises(ValueError, match="empty order"):
        finalize_order_and_generate_invoice(db_conn, order_id)

    # Verify order is still Draft and no invoice exists
    order = db_conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    assert order["status"] == "Draft"
    inv_cnt = db_conn.execute("SELECT COUNT(*) FROM invoices WHERE order_id = ?", (order_id,)).fetchone()[0]
    assert inv_cnt == 0

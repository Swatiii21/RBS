"""Billing and Invoice Calculation Service with Decimal-Precision Arithmetic.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides:
- Exact financial arithmetic using Python's Decimal class and ROUND_HALF_UP
  to eliminate floating-point representation anomalies.
- Centralized calculation sequence matching Course TQM specifications:
    1. Line Total = quantity * unit_price
    2. Subtotal = sum of all Line Totals
    3. Discount Amount = Subtotal * (Discount Rate / 100)
    4. Taxable Amount = Subtotal - Discount Amount
    5. Tax Amount = Taxable Amount * (Tax Rate / 100)
    6. Grand Total = Taxable Amount + Tax Amount
- Configurable tax rate and server-enforced discount ceilings.
- Transaction-safe invoice finalization guaranteeing atomicity (ACID).
- Invoices are immutable once finalized.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR
from typing import Any, Dict, List, Optional, Tuple
import sqlite3

from app.database.connection import transaction
from app.services.logging_service import log_activity
from app.services.settings_service import get_setting

# Standard two-decimal currency precision quantum
TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class BillingCalculation:
    """Immutable data container for exact billing breakdown."""

    subtotal: Decimal
    discount_rate: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    grand_total: Decimal

    def to_dict(self) -> Dict[str, float]:
        """Convert Decimal values to float representation for JSON/Template display."""
        return {
            "subtotal": float(self.subtotal),
            "discount_rate": float(self.discount_rate),
            "discount_amount": float(self.discount_amount),
            "taxable_amount": float(self.taxable_amount),
            "tax_rate": float(self.tax_rate),
            "tax_amount": float(self.tax_amount),
            "grand_total": float(self.grand_total),
        }


def round_currency(value: Decimal, rounding_policy: str = "ROUND_HALF_UP") -> Decimal:
    """Round a Decimal amount to 2 decimal places using configured rounding rule.

    Args:
        value: Exact Decimal quantity.
        rounding_policy: 'ROUND_HALF_UP', 'ROUND_CEIL', or 'ROUND_FLOOR'.

    Returns:
        Decimal rounded to two decimal places (e.g. 125.50).
    """
    mode = ROUND_HALF_UP
    if rounding_policy == "ROUND_CEIL":
        mode = ROUND_CEILING
    elif rounding_policy == "ROUND_FLOOR":
        mode = ROUND_FLOOR

    return value.quantize(TWO_PLACES, rounding=mode)


def calculate_billing_breakdown(
    items: List[Dict[str, Any]],
    discount_rate: float | Decimal | str,
    tax_rate: float | Decimal | str,
    max_discount_limit: float | Decimal | str = 25.0,
    rounding_policy: str = "ROUND_HALF_UP",
) -> BillingCalculation:
    """Calculate billing amounts strictly using Decimal arithmetic.

    Args:
        items: List of dictionaries with 'quantity' and 'unit_price'.
        discount_rate: Applied discount percentage (e.g. 10.0 for 10%).
        tax_rate: Applied tax percentage (e.g. 5.0 for 5% GST/VAT).
        max_discount_limit: Server-enforced maximum discount ceiling.
        rounding_policy: Rounding strategy string.

    Returns:
        BillingCalculation: Complete calculated breakdown.

    Raises:
        ValueError: If negative values or discount exceeds policy limit.
    """
    d_rate = Decimal(str(discount_rate))
    t_rate = Decimal(str(tax_rate))
    max_disc = Decimal(str(max_discount_limit))

    # Strict server validation
    if d_rate < Decimal("0.0"):
        raise ValueError("Discount rate cannot be negative.")
    if d_rate > max_disc:
        raise ValueError(
            f"Discount rate of {d_rate}% exceeds configured maximum allowed discount limit of {max_disc}%."
        )
    if t_rate < Decimal("0.0"):
        raise ValueError("Tax rate cannot be negative.")

    # 1 & 2. Calculate line totals and subtotal
    subtotal = Decimal("0.00")
    for item in items:
        qty = Decimal(str(item.get("quantity", 0)))
        price = Decimal(str(item.get("unit_price", 0.0)))
        if qty <= Decimal("0"):
            raise ValueError(f"Item quantity must be greater than zero, got {qty}.")
        if price < Decimal("0"):
            raise ValueError(f"Item unit price cannot be negative, got {price}.")
        line_total = round_currency(qty * price, rounding_policy)
        subtotal += line_total

    subtotal = round_currency(subtotal, rounding_policy)

    # 3. Apply configured discount
    raw_discount_amt = subtotal * (d_rate / Decimal("100.0"))
    discount_amount = round_currency(raw_discount_amt, rounding_policy)

    # 4. Taxable amount
    taxable_amount = round_currency(subtotal - discount_amount, rounding_policy)
    if taxable_amount < Decimal("0.0"):
        taxable_amount = Decimal("0.00")

    # 5. Calculate tax on taxable amount
    raw_tax_amt = taxable_amount * (t_rate / Decimal("100.0"))
    tax_amount = round_currency(raw_tax_amt, rounding_policy)

    # 6. Final grand total
    grand_total = round_currency(taxable_amount + tax_amount, rounding_policy)

    return BillingCalculation(
        subtotal=subtotal,
        discount_rate=d_rate,
        discount_amount=discount_amount,
        taxable_amount=taxable_amount,
        tax_rate=t_rate,
        tax_amount=tax_amount,
        grand_total=grand_total,
    )


def generate_invoice_number(conn: sqlite3.Connection, prefix: str = "INV-") -> str:
    """Generate the next unique sequential invoice number (e.g. INV-2026-0001).

    Args:
        conn: SQLite connection.
        prefix: Configurable prefix string.

    Returns:
        str: Unique invoice number.
    """
    year = datetime.now().year
    year_prefix = f"{prefix}{year}-"
    cursor = conn.cursor()
    cursor.execute(
        "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{year_prefix}%",),
    )
    row = cursor.fetchone()
    if row:
        last_num_str = row["invoice_number"].replace(year_prefix, "")
        try:
            seq = int(last_num_str) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{year_prefix}{seq:04d}"


def finalize_order_and_generate_invoice(
    conn: sqlite3.Connection,
    order_id: int,
    actor: str = "Staff",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Atomically finalize an order and issue an immutable invoice using an ACID transaction.

    Ensures that order status change and invoice record creation succeed together,
    preventing inconsistent intermediate states or orphan invoices.

    Args:
        conn: SQLite connection.
        order_id: Order primary key.
        actor: Operator finalizing the invoice.
        notes: Optional billing notes.

    Returns:
        Dict[str, Any]: Details of the generated invoice.

    Raises:
        ValueError: If order is not in 'Draft' state or contains no items.
    """
    cursor = conn.cursor()

    # Verify order state
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    if not order:
        raise ValueError(f"Order #{order_id} does not exist.")

    if order["status"] != "Draft":
        raise ValueError(
            f"Cannot finalize Order #{order['order_number']}: status is already '{order['status']}'."
        )

    # Fetch order items
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    items = cursor.fetchall()
    if not items:
        raise ValueError("Cannot finalize an empty order with no items.")

    # Retrieve current configured parameters
    prefix = get_setting(conn, "invoice_prefix", "INV-")
    rest_name = get_setting(conn, "restaurant_name", "Emerald Dine Restaurant")
    rest_addr = get_setting(conn, "address", "124 Parkview Avenue, Dehradun")
    rest_contact = get_setting(conn, "contact_number", "+91 98765 43210")
    rounding_policy = get_setting(conn, "rounding_policy", "ROUND_HALF_UP")

    invoice_num = generate_invoice_number(conn, prefix=prefix)
    now = datetime.now(timezone.utc).isoformat()

    # Execute transactional commit
    with transaction(conn) as tx:
        # Mark order Finalized
        tx.execute(
            "UPDATE orders SET status = 'Finalized', updated_at = ? WHERE id = ?",
            (now, order_id),
        )

        # Insert immutable invoice
        tx.execute(
            """
            INSERT INTO invoices (
                invoice_number, order_id, restaurant_name, restaurant_address, restaurant_contact,
                invoice_date, subtotal, discount_rate, discount_amount, taxable_amount,
                tax_rate, tax_amount, grand_total, rounding_policy, status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?)
            """,
            (
                invoice_num,
                order_id,
                rest_name,
                rest_addr,
                rest_contact,
                now,
                order["subtotal"],
                order["discount_rate"],
                order["discount_amount"],
                order["taxable_amount"],
                order["tax_rate"],
                order["tax_amount"],
                order["grand_total"],
                rounding_policy,
                notes,
                now,
            ),
        )

    # Log business audit trail
    log_activity(
        conn=conn,
        action_type="INVOICE_FINALIZE",
        module="Billing",
        description=f"Finalized invoice {invoice_num} for order {order['order_number']} (Grand Total: {order['grand_total']})",
        actor=actor,
        affected_record_id=invoice_num,
        outcome="Success",
    )

    return {
        "invoice_number": invoice_num,
        "order_number": order["order_number"],
        "grand_total": order["grand_total"],
        "finalized_at": now,
    }


def get_invoice_by_number(conn: sqlite3.Connection, invoice_number: str) -> Optional[Dict[str, Any]]:
    """Retrieve full invoice document including line items and restaurant profile.

    Args:
        conn: SQLite connection.
        invoice_number: Unique invoice number.

    Returns:
        Optional[Dict[str, Any]]: Complete invoice data structure or None.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT i.*, o.order_number, o.order_type, o.table_number, o.customer_name, o.customer_contact
        FROM invoices i
        JOIN orders o ON i.order_id = o.id
        WHERE i.invoice_number = ?
        """,
        (invoice_number,),
    )
    invoice = cursor.fetchone()
    if not invoice:
        return None

    # Fetch order items
    cursor.execute(
        "SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC",
        (invoice["order_id"],),
    )
    items = cursor.fetchall()

    footer_text = get_setting(
        conn,
        "invoice_footer_text",
        "Thank you for dining with us! Please visit again. TQM Certified.",
    )
    currency_symbol = get_setting(conn, "currency_symbol", "₹")
    gst_number = get_setting(conn, "gst_number", "07AABCG1234F1Z9")

    return {
        "invoice": invoice,
        "items": items,
        "footer_text": footer_text,
        "currency_symbol": currency_symbol,
        "gst_number": gst_number,
    }


def get_invoices_history(
    conn: sqlite3.Connection,
    search: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    per_page: int = 15,
) -> Tuple[List[sqlite3.Row], int]:
    """Retrieve paginated and filtered historical invoices.

    Args:
        conn: SQLite connection.
        search: Optional search term matching invoice number or customer name.
        status: Optional invoice status filter ('Active', 'Cancelled', 'Corrected').
        start_date: Optional lower bound date filter (YYYY-MM-DD).
        end_date: Optional upper bound date filter (YYYY-MM-DD).
        page: Page number.
        per_page: Items per page.

    Returns:
        Tuple[List[sqlite3.Row], int]: Filtered invoice rows and total count.
    """
    conditions = []
    params: List[Any] = []

    if search:
        conditions.append("(i.invoice_number LIKE ? OR o.customer_name LIKE ? OR o.order_number LIKE ?)")
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    if status:
        conditions.append("i.status = ?")
        params.append(status)

    if start_date:
        conditions.append("DATE(i.invoice_date) >= DATE(?)")
        params.append(start_date)

    if end_date:
        conditions.append("DATE(i.invoice_date) <= DATE(?)")
        params.append(end_date)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    cursor = conn.cursor()
    count_query = f"""
        SELECT COUNT(*) AS total
        FROM invoices i
        JOIN orders o ON i.order_id = o.id
        {where_clause}
    """
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()["total"]

    offset = max(0, (page - 1) * per_page)
    data_query = f"""
        SELECT i.*, o.order_number, o.order_type, o.table_number, o.customer_name
        FROM invoices i
        JOIN orders o ON i.order_id = o.id
        {where_clause}
        ORDER BY i.id DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(data_query, params + [per_page, offset])
    rows = cursor.fetchall()

    return rows, total_count

"""Menu Management Service.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

Provides:
- Complete CRUD operations for restaurant menu catalog.
- Robust server-side validation rejecting negative prices, empty names, and duplicate items.
- Safe deletion guards preventing removal of items with active historical billing links.
- Filter and search capabilities.
- Audit logging for all creation, update, and deactivation events.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import sqlite3

from app.services.logging_service import log_activity


def get_categories(conn: sqlite3.Connection) -> List[str]:
    """Retrieve distinct list of existing menu categories.

    Args:
        conn: SQLite connection.

    Returns:
        List[str]: Alphabetically ordered list of category names.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM menu_items ORDER BY category ASC")
    return [row["category"] for row in cursor.fetchall() if row["category"]]


def get_menu_items(
    conn: sqlite3.Connection,
    search: Optional[str] = None,
    category: Optional[str] = None,
    available_only: bool = False,
    page: int = 1,
    per_page: int = 50,
) -> Tuple[List[sqlite3.Row], int]:
    """Retrieve filtered and paginated list of menu items.

    Args:
        conn: SQLite connection.
        search: Optional substring match on name or item_code.
        category: Optional category filter.
        available_only: If True, only returns items marked available.
        page: Page number (1-indexed).
        per_page: Number of items per page.

    Returns:
        Tuple[List[sqlite3.Row], int]: List of matching items and total count.
    """
    conditions = []
    params: List[Any] = []

    if search:
        conditions.append("(name LIKE ? OR item_code LIKE ?)")
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard])

    if category:
        conditions.append("category = ?")
        params.append(category)

    if available_only:
        conditions.append("is_available = 1")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) AS total FROM menu_items{where_clause}", params)
    total_count = cursor.fetchone()["total"]

    offset = max(0, (page - 1) * per_page)
    cursor.execute(
        f"""
        SELECT * FROM menu_items{where_clause}
        ORDER BY category ASC, name ASC
        LIMIT ? OFFSET ?
        """,
        params + [per_page, offset],
    )
    rows = cursor.fetchall()
    return rows, total_count


def get_menu_item_by_id(conn: sqlite3.Connection, item_id: int) -> Optional[sqlite3.Row]:
    """Retrieve a single menu item by primary key.

    Args:
        conn: SQLite connection.
        item_id: Primary key ID.

    Returns:
        Optional[sqlite3.Row]: Menu item record or None.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,))
    return cursor.fetchone()


def validate_menu_item_data(
    name: str,
    category: str,
    unit_price: float | str,
) -> float:
    """Validate menu item fields before persistence.

    Args:
        name: Name of dish/item.
        category: Menu category.
        unit_price: Unit price value.

    Returns:
        float: Validated unit price.

    Raises:
        ValueError: If validation rules are violated.
    """
    if not name or not name.strip():
        raise ValueError("Item name is required and cannot be blank.")

    if not category or not category.strip():
        raise ValueError("Category is required.")

    try:
        price = float(unit_price)
    except (ValueError, TypeError) as err:
        raise ValueError("Unit price must be a valid positive number.") from err

    if price < 0.0:
        raise ValueError("Unit price cannot be negative.")

    return round(price, 2)


def generate_item_code(conn: sqlite3.Connection) -> str:
    """Generate next available sequential item code (e.g. M-115).

    Args:
        conn: SQLite connection.

    Returns:
        str: Unique item code.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM menu_items ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    next_id = (row["id"] + 1) if row else 101
    return f"M-{next_id:03d}"


def create_menu_item(
    conn: sqlite3.Connection,
    name: str,
    category: str,
    unit_price: float | str,
    description: Optional[str] = None,
    item_code: Optional[str] = None,
    is_available: int = 1,
    actor: str = "Staff",
) -> int:
    """Create a new menu item with uniqueness and price boundary checks.

    Args:
        conn: SQLite connection.
        name: Item name.
        category: Item category.
        unit_price: Price in currency units.
        description: Optional details.
        item_code: Optional custom code; auto-generated if omitted.
        is_available: Availability toggle (1 or 0).
        actor: User initiating creation.

    Returns:
        int: Primary key ID of created menu item.

    Raises:
        ValueError: On validation error or duplicate item name.
    """
    price = validate_menu_item_data(name, category, unit_price)
    clean_name = name.strip()
    clean_category = category.strip()
    clean_desc = description.strip() if description else ""

    cursor = conn.cursor()
    # Uniqueness check: prevent duplicate menu item name in same category
    cursor.execute(
        "SELECT id FROM menu_items WHERE LOWER(name) = LOWER(?) AND LOWER(category) = LOWER(?)",
        (clean_name, clean_category),
    )
    if cursor.fetchone():
        raise ValueError(
            f"A menu item with name '{clean_name}' already exists in category '{clean_category}'."
        )

    if not item_code or not item_code.strip():
        code = generate_item_code(conn)
    else:
        code = item_code.strip().upper()
        # Verify code uniqueness
        cursor.execute("SELECT id FROM menu_items WHERE item_code = ?", (code,))
        if cursor.fetchone():
            raise ValueError(f"Item code '{code}' is already assigned to another item.")

    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO menu_items (
            item_code, name, category, description, unit_price, is_available, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (code, clean_name, clean_category, clean_desc, price, 1 if is_available else 0, now, now),
    )
    conn.commit()
    item_id = cursor.lastrowid

    log_activity(
        conn=conn,
        action_type="MENU_CREATE",
        module="Menu",
        description=f"Created menu item '{clean_name}' ({code}) priced at {price}",
        actor=actor,
        affected_record_id=str(item_id),
        outcome="Success",
    )
    return item_id


def update_menu_item(
    conn: sqlite3.Connection,
    item_id: int,
    name: str,
    category: str,
    unit_price: float | str,
    description: Optional[str] = None,
    is_available: int = 1,
    actor: str = "Staff",
) -> None:
    """Update existing menu item information.

    Args:
        conn: SQLite connection.
        item_id: ID of item to update.
        name: Updated name.
        category: Updated category.
        unit_price: Updated price.
        description: Updated description.
        is_available: Availability status.
        actor: User initiating update.

    Raises:
        ValueError: If item is not found or validation fails.
    """
    item = get_menu_item_by_id(conn, item_id)
    if not item:
        raise ValueError(f"Menu item with ID {item_id} does not exist.")

    price = validate_menu_item_data(name, category, unit_price)
    clean_name = name.strip()
    clean_category = category.strip()
    clean_desc = description.strip() if description else ""

    cursor = conn.cursor()
    # Check for duplicate name conflicts with other items
    cursor.execute(
        """
        SELECT id FROM menu_items
        WHERE LOWER(name) = LOWER(?) AND LOWER(category) = LOWER(?) AND id != ?
        """,
        (clean_name, clean_category, item_id),
    )
    if cursor.fetchone():
        raise ValueError(
            f"Another item named '{clean_name}' already exists in category '{clean_category}'."
        )

    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        UPDATE menu_items
        SET name = ?, category = ?, description = ?, unit_price = ?,
            is_available = ?, updated_at = ?
        WHERE id = ?
        """,
        (clean_name, clean_category, clean_desc, price, 1 if is_available else 0, now, item_id),
    )
    conn.commit()

    log_activity(
        conn=conn,
        action_type="MENU_UPDATE",
        module="Menu",
        description=f"Updated menu item #{item_id} ('{clean_name}') - Price: {price}, Available: {bool(is_available)}",
        actor=actor,
        affected_record_id=str(item_id),
        outcome="Success",
    )


def deactivate_menu_item(conn: sqlite3.Connection, item_id: int, actor: str = "Staff") -> None:
    """Deactivate a menu item so it cannot be added to new orders.

    Args:
        conn: SQLite connection.
        item_id: ID of item.
        actor: User initiating deactivation.
    """
    item = get_menu_item_by_id(conn, item_id)
    if not item:
        raise ValueError(f"Menu item with ID {item_id} not found.")

    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE menu_items SET is_available = 0, updated_at = ? WHERE id = ?",
        (now, item_id),
    )
    conn.commit()

    log_activity(
        conn=conn,
        action_type="MENU_DEACTIVATE",
        module="Menu",
        description=f"Deactivated menu item #{item_id} ('{item['name']}')",
        actor=actor,
        affected_record_id=str(item_id),
        outcome="Success",
    )


def delete_menu_item(conn: sqlite3.Connection, item_id: int, actor: str = "Staff") -> None:
    """Delete a menu item only if it has never been ordered in any bill.

    If historical orders reference this item, deletion is blocked to preserve
    financial integrity; user is instructed to deactivate instead.

    Args:
        conn: SQLite connection.
        item_id: ID of item to delete.
        actor: User initiating deletion.

    Raises:
        ValueError: If item is referenced in historical orders.
    """
    item = get_menu_item_by_id(conn, item_id)
    if not item:
        raise ValueError(f"Menu item with ID {item_id} not found.")

    cursor = conn.cursor()
    # Check historical order usage
    cursor.execute("SELECT COUNT(*) AS cnt FROM order_items WHERE menu_item_id = ?", (item_id,))
    history_count = cursor.fetchone()["cnt"]

    if history_count > 0:
        raise ValueError(
            f"Cannot delete item '{item['name']}' because it appears in {history_count} historical order records. "
            f"Please deactivate the item instead to preserve historical billing integrity."
        )

    cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()

    log_activity(
        conn=conn,
        action_type="MENU_DELETE",
        module="Menu",
        description=f"Permanently deleted unused menu item #{item_id} ('{item['name']}')",
        actor=actor,
        affected_record_id=str(item_id),
        outcome="Success",
    )

-- ==============================================================================
-- RESTAURANT BILLING SYSTEM - RELATIONAL DATABASE SCHEMA (SQLite3)
-- Course: BBAT104 - Fundamentals of Total Quality Management (TQM)
-- Assigned Quality Goal: Q11 - Improve Maintainability
-- Student: Swati Melkani (CSE - B, 2026-27)
-- ==============================================================================

-- Enforce Foreign Keys explicitly
PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. MENU ITEMS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    unit_price REAL NOT NULL CHECK(unit_price >= 0.0),
    is_available INTEGER NOT NULL DEFAULT 1 CHECK(is_available IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_menu_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_menu_available ON menu_items(is_available);
CREATE INDEX IF NOT EXISTS idx_menu_name ON menu_items(name);

-- ------------------------------------------------------------------------------
-- 2. ORDERS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL UNIQUE,
    order_type TEXT NOT NULL CHECK(order_type IN ('Dine-in', 'Takeaway')),
    table_number TEXT,
    customer_name TEXT,
    customer_contact TEXT,
    status TEXT NOT NULL DEFAULT 'Draft' CHECK(status IN ('Draft', 'Finalized', 'Cancelled')),
    subtotal REAL NOT NULL DEFAULT 0.0 CHECK(subtotal >= 0.0),
    discount_rate REAL NOT NULL DEFAULT 0.0 CHECK(discount_rate >= 0.0 AND discount_rate <= 100.0),
    discount_amount REAL NOT NULL DEFAULT 0.0 CHECK(discount_amount >= 0.0),
    taxable_amount REAL NOT NULL DEFAULT 0.0 CHECK(taxable_amount >= 0.0),
    tax_rate REAL NOT NULL DEFAULT 0.0 CHECK(tax_rate >= 0.0),
    tax_amount REAL NOT NULL DEFAULT 0.0 CHECK(tax_amount >= 0.0),
    grand_total REAL NOT NULL DEFAULT 0.0 CHECK(grand_total >= 0.0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);

-- ------------------------------------------------------------------------------
-- 3. ORDER ITEMS TABLE
-- Preserves item_name and historical unit_price at time of order
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER,
    item_name TEXT NOT NULL,
    unit_price REAL NOT NULL CHECK(unit_price >= 0.0),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    line_total REAL NOT NULL CHECK(line_total >= 0.0),
    created_at TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

-- ------------------------------------------------------------------------------
-- 4. INVOICES TABLE
-- Immutable finalized billing documents
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT NOT NULL UNIQUE,
    order_id INTEGER NOT NULL UNIQUE,
    restaurant_name TEXT NOT NULL,
    restaurant_address TEXT NOT NULL,
    restaurant_contact TEXT NOT NULL,
    invoice_date TEXT NOT NULL,
    subtotal REAL NOT NULL CHECK(subtotal >= 0.0),
    discount_rate REAL NOT NULL CHECK(discount_rate >= 0.0),
    discount_amount REAL NOT NULL CHECK(discount_amount >= 0.0),
    taxable_amount REAL NOT NULL CHECK(taxable_amount >= 0.0),
    tax_rate REAL NOT NULL CHECK(tax_rate >= 0.0),
    tax_amount REAL NOT NULL CHECK(tax_amount >= 0.0),
    grand_total REAL NOT NULL CHECK(grand_total >= 0.0),
    rounding_policy TEXT NOT NULL DEFAULT 'ROUND_HALF_UP',
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Cancelled', 'Corrected')),
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);

-- ------------------------------------------------------------------------------
-- 5. SYSTEM SETTINGS TABLE (Editable through UI without code edits)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    section TEXT NOT NULL,
    description TEXT,
    updated_by TEXT DEFAULT 'Administrator',
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_settings_section ON system_settings(section);

-- ------------------------------------------------------------------------------
-- 6. ACTIVITY LOGS TABLE (Business audit trail stored in DB)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'Staff',
    action_type TEXT NOT NULL,
    module TEXT NOT NULL,
    affected_record_id TEXT,
    outcome TEXT NOT NULL CHECK(outcome IN ('Success', 'Failure', 'Warning')),
    description TEXT NOT NULL,
    correlation_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_module ON activity_logs(module);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action_type);

-- ------------------------------------------------------------------------------
-- 7. QUALITY DEFECTS TABLE (TQM Defect Checksheet)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quality_defects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    defect_code TEXT NOT NULL UNIQUE,
    date_reported TEXT NOT NULL,
    affected_module TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('Critical', 'High', 'Medium', 'Low')),
    occurrence_count INTEGER NOT NULL DEFAULT 1 CHECK(occurrence_count > 0),
    root_cause_category TEXT NOT NULL,
    corrective_action TEXT,
    status TEXT NOT NULL DEFAULT 'Reported' CHECK(status IN ('Reported', 'Investigating', 'Fix Implemented', 'Verified', 'Closed')),
    resolution_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_defects_module ON quality_defects(affected_module);
CREATE INDEX IF NOT EXISTS idx_defects_category ON quality_defects(category);
CREATE INDEX IF NOT EXISTS idx_defects_status ON quality_defects(status);

-- ------------------------------------------------------------------------------
-- 8. QUALITY IMPROVEMENTS TABLE (TQM PDCA Continuous Improvement Register)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quality_improvements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    plan_problem TEXT NOT NULL,
    plan_objective TEXT NOT NULL,
    plan_action TEXT NOT NULL,
    do_implemented_change TEXT,
    do_linked_defect TEXT,
    check_retest_results TEXT,
    check_metrics_comparison TEXT,
    act_decision TEXT CHECK(act_decision IN ('Accepted', 'Revised', 'Reopened', 'Pending')),
    act_lessons_learned TEXT,
    owner TEXT NOT NULL,
    target_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Plan' CHECK(status IN ('Plan', 'Do', 'Check', 'Act', 'Completed')),
    updated_at TEXT NOT NULL
);

-- ------------------------------------------------------------------------------
-- 9. FMEA RECORDS TABLE (Failure Mode and Effects Analysis Register)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fmea_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_step TEXT NOT NULL,
    potential_failure_mode TEXT NOT NULL,
    potential_effect TEXT NOT NULL,
    potential_cause TEXT NOT NULL,
    existing_controls TEXT NOT NULL,
    severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 10),
    occurrence INTEGER NOT NULL CHECK(occurrence BETWEEN 1 AND 10),
    detection INTEGER NOT NULL CHECK(detection BETWEEN 1 AND 10),
    recommended_mitigation TEXT NOT NULL,
    responsible_role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open', 'Mitigated', 'Closed')),
    updated_at TEXT NOT NULL
);

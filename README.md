# Restaurant Billing System — TQM Q11: Improve Maintainability

**Academic Course:** BBAT104 — Fundamentals of Total Quality Management (TQM)  
**Academic Session:** 2026–27  
**Student:** Swati Melkani  
**Branch & Section:** CSE, Section B  
**Assigned Quality Goal:** Q11 — Improve Maintainability  

---

## 1. Project Overview

The **Restaurant Billing System (RBS)** is a complete, modular, responsive web application engineered to streamline daily restaurant billing operations while rigorously demonstrating the **TQM Q11: Improve Maintainability** quality objective.

Built according to the BBAT104 course specifications, this project avoids monolithic code, hardcoded business values, and opaque calculations. It features a complete relational SQLite database, Decimal-based financial calculation engine, ACID transactional invoice finalization, dynamic system settings, dual-layer audit/diagnostic logging, and an interactive **TQM Quality Analytics Hub** with Defect Checksheets, Pareto (80/20) charts, FMEA risk matrices, Ishikawa Fishbone root-cause taxonomy, SIPOC process mapping, and PDCA continuous improvement tracking.

---

## 2. Five Mandatory Q11 Maintainability Features

| # | Q11 Assigned Feature | Architectural Implementation | Practical User Benefit |
|---|----------------------|------------------------------|------------------------|
| **1** | **Modular Structure** | Separated into distinct layers (`app/routes/`, `app/services/`, `app/database/`, `app/templates/`, `app/static/`). | High cohesion, loose coupling; developers can modify billing rules without altering UI routes. |
| **2** | **Configuration Files** | Centralized in `app/config.py`, `.env.example`, `.env`, and `config/settings.example.json`. | Technical environment parameters (DB path, log level, secret key) separated from source code. |
| **3** | **System Settings** | Dedicated `system_settings` SQLite table with administrative UI at `/settings`. | Non-programmers can adjust tax rates, maximum discounts, currency symbols, and invoice footers without restarting the server or editing code. |
| **4** | **Activity Logs** | Dual-tier logging: business audit events in `activity_logs` table (UI searchable at `/logs`), technical diagnostics in rotating file `logs/app.log`. | Full traceability of all user actions; sensitive credentials (passwords, tokens) automatically sanitized/redacted. |
| **5** | **Code Comments** | Comprehensive docstrings, Python type hints, mathematical formulas documented with Decimal quantization logic. | Future maintainability, rapid onboarding, and clear explanation of design decisions for academic evaluation. |

---

## 3. Technology Stack

- **Backend Framework:** Python 3 (Flask 3.1.x)
- **Frontend / Styling:** HTML5, CSS3, Bootstrap 5.3.3, Bootstrap Icons, Custom Emerald Theme
- **Data Persistence:** SQLite3 with `PRAGMA foreign_keys = ON;` and WAL journal mode
- **Financial Arithmetic:** Python `decimal.Decimal` with `ROUND_HALF_UP` quantization
- **Interactive Visualizations:** Chart.js 4.4.x (Pareto dual-axis chart, sales trend, top items)
- **Automated Testing:** pytest 8.3.x (with isolated in-memory test database)
- **Environment Management:** python-dotenv

---

## 4. Architecture & Directory Structure

```text
restaurant-billing-system/
├── app/
│   ├── __init__.py               # Application factory & centralized error handlers
│   ├── config.py                 # Central configuration classes (Dev, Test, Prod)
│   ├── database/
│   │   ├── __init__.py           # Database connection helpers & transaction context
│   │   ├── connection.py         # Thread-safe SQLite connection & foreign key pragma
│   │   ├── schema.sql            # Relational database DDL schema with indexes
│   │   └── migrations.py         # Idempotent DB setup & sample baseline seed
│   ├── services/
│   │   ├── __init__.py           # Service layer package index
│   │   ├── menu_service.py       # Menu item CRUD, validation, and safe-deletion checks
│   │   ├── order_service.py      # Order lifecycle (Draft -> Finalized/Cancelled) & cart logic
│   │   ├── billing_service.py    # Decimal billing arithmetic & ACID invoice finalization
│   │   ├── settings_service.py   # System settings cache, batch updates, and validation
│   │   ├── logging_service.py    # Dual audit/diagnostic logging & sensitive sanitization
│   │   └── quality_service.py    # TQM tools: Defect checksheet, Pareto, FMEA, PDCA
│   ├── routes/
│   │   ├── __init__.py           # Blueprint registrar
│   │   ├── dashboard.py          # Operational dashboard & live revenue metrics
│   │   ├── menu.py               # Menu catalog HTTP route handlers
│   │   ├── orders.py             # POS order cart HTTP route handlers
│   │   ├── billing.py            # Invoice finalization, print view, & history search
│   │   ├── settings.py           # Administrative system settings UI
│   │   ├── activity_logs.py      # Business audit log inspection UI
│   │   └── quality.py            # TQM Quality Hub, Checksheet, Pareto, FMEA, PDCA
│   ├── templates/
│   │   ├── base.html             # Master layout with responsive sidebar & topbar
│   │   ├── dashboard.html        # Live KPI cards, sales trend, and top items charts
│   │   ├── menu/                 # Menu index and item form
│   │   ├── orders/               # Orders ledger, ticket creator, and POS workstation
│   │   ├── billing/              # Invoice ledger and official printable tax receipt
│   │   ├── settings/             # Dynamic system settings manager
│   │   ├── logs/                 # Business audit trail viewer
│   │   ├── quality/              # TQM hub, checksheet, Pareto chart, FMEA, Fishbone, SIPOC, PDCA
│   │   └── errors/               # Friendly 400, 404, 500 error views
│   └── static/
│       ├── css/style.css         # Custom emerald-green stylesheet & print media styles
│       └── js/main.js            # Client-side validation, alerts, and print handlers
├── config/
│   └── settings.example.json     # Baseline configuration example template
├── docs/
│   ├── SRS.md                    # Software Requirements Specification
│   ├── architecture.md           # Architectural documentation, ER diagram & checklist
│   ├── user_manual.md            # Step-by-step user and operator guide
│   ├── TQM_REPORT.md             # BBAT104 Course Quality Project Report
│   ├── FMEA.md                   # Failure Mode and Effects Analysis Register
│   └── TEST_CASES.md             # Test cases matrix with actual execution evidence
├── instance/                     # SQLite database files (excluded from Git)
├── logs/                         # Rotating application log files (excluded from Git)
├── tests/
│   ├── conftest.py               # Pytest fixtures & isolated in-memory test database
│   ├── test_menu.py              # Menu validation and CRUD test suite
│   ├── test_orders.py            # Order management and lifecycle test suite
│   ├── test_billing.py           # Financial calculation, rounding, and ACID tests
│   ├── test_settings.py          # Dynamic settings and config validation tests
│   ├── test_activity_logs.py     # Audit logging and payload sanitization tests
│   └── test_quality.py           # TQM Pareto, FMEA RPN, and defect checksheet tests
├── .env.example                  # Environment variable blueprint
├── .gitignore                    # Git ignore file for Python, logs, and databases
├── requirements.txt              # Pinned Python package dependencies
├── run.py                        # Application entry point
└── README.md                     # Comprehensive project documentation
```

---

## 5. Installation and Setup Instructions (Windows PowerShell)

### Step 1: Open Terminal in Workspace
```powershell
cd c:\Users\HP\Downloads\RBS
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Local Environment
```powershell
# Copy the example environment file if .env does not already exist
Copy-Item .env.example .env
```

---

## 6. Running the Application

Execute the entry point:
```powershell
python run.py
```

The system will start and display:
```text
========================================================================
  RESTAURANT BILLING SYSTEM — TQM Q11: IMPROVE MAINTAINABILITY
  Student: Swati Melkani | CSE - Section B | Academic Session: 2026-27
  Course : BBAT104 — Fundamentals of Total Quality Management (TQM)
  Status : Running at http://127.0.0.1:5000/
========================================================================
```

Open your browser and navigate to: **`http://127.0.0.1:5000/`**

---

## 7. Running Automated Test Suite

All 28 unit and integration tests run against an isolated in-memory test database to prevent polluting the live database:

```powershell
.\venv\Scripts\python -m pytest -v
```

### Actual Test Execution Output:
```text
tests/test_activity_logs.py::test_log_business_activity PASSED           [  3%]
tests/test_activity_logs.py::test_sensitive_payload_sanitization PASSED  [  7%]
tests/test_activity_logs.py::test_activity_log_filtering PASSED          [ 10%]
tests/test_billing.py::test_billing_calculation_accuracy PASSED          [ 14%]
tests/test_billing.py::test_monetary_rounding_policy PASSED              [ 17%]
tests/test_billing.py::test_reject_discount_exceeding_configured_maximum PASSED [ 21%]
tests/test_billing.py::test_reject_negative_quantity_in_billing PASSED   [ 25%]
tests/test_billing.py::test_preserve_historical_price_after_menu_change PASSED [ 28%]
tests/test_billing.py::test_rollback_on_failed_finalization PASSED       [ 32%]
tests/test_menu.py::test_create_valid_menu_item PASSED                   [ 35%]
tests/test_menu.py::test_reject_negative_price PASSED                    [ 39%]
tests/test_menu.py::test_prevent_duplicate_menu_item PASSED              [ 42%]
tests/test_menu.py::test_update_existing_menu_item PASSED                [ 46%]
tests/test_menu.py::test_deactivate_menu_item PASSED                     [ 50%]
tests/test_menu.py::test_safe_delete_blocks_ordered_items PASSED         [ 53%]
tests/test_orders.py::test_create_order_lifecycle PASSED                 [ 57%]
tests/test_orders.py::test_update_quantity_and_remove_item PASSED        [ 60%]
tests/test_orders.py::test_prevent_editing_finalized_order PASSED        [ 64%]
tests/test_orders.py::test_cancel_order_workflow PASSED                  [ 67%]
tests/test_quality.py::test_create_and_update_defect PASSED              [ 71%]
tests/test_quality.py::test_fmea_rpn_calculation PASSED                  [ 75%]
tests/test_quality.py::test_pareto_analysis_calculation PASSED           [ 78%]
tests/test_quality.py::test_empty_pareto_dataset_handling PASSED         [ 82%]
tests/test_settings.py::test_load_default_settings PASSED                [ 85%]
tests/test_settings.py::test_update_and_reload_setting PASSED            [ 89%]
tests/test_settings.py::test_reject_invalid_setting_values PASSED        [ 92%]
tests/test_settings.py::test_settings_change_audit_logging PASSED        [ 96%]
tests/test_settings.py::test_config_class_validation PASSED              [100%]

============================= 28 passed in 0.19s ==============================
```

---

## 8. Financial Calculation & Rounding Policy

The system uses standard Decimal arithmetic:
$$\text{Line Total} = \text{quantize}(\text{quantity} \times \text{unit\_price})$$
$$\text{Subtotal} = \sum \text{Line Totals}$$
$$\text{Discount Amount} = \text{quantize}\left(\text{Subtotal} \times \frac{\text{Discount Rate}}{100}\right)$$
$$\text{Taxable Amount} = \text{Subtotal} - \text{Discount Amount}$$
$$\text{Tax Amount} = \text{quantize}\left(\text{Taxable Amount} \times \frac{\text{Tax Rate}}{100}\right)$$
$$\text{Grand Total} = \text{Taxable Amount} + \text{Tax Amount}$$

- **Rounding Rule:** `ROUND_HALF_UP` (standard commercial rule where half-paisa rounds upwards).
- **Price Integrity:** Unit prices are snapshot into `order_items` at the time of order, ensuring that subsequent changes to the menu catalog never silently alter past accounting records.

---

## 9. TQM Implementation Summary

1. **Defect Checksheet (`/quality/defects`):** Standardizes defect logging, categorization, severity assignment, and lifecycle resolution.
2. **Pareto Analysis (`/quality/pareto`):** Calculates cumulative frequencies and percentages, identifying the vital few defect categories that drive the majority of system failures.
3. **Ishikawa / Fishbone (`/quality/fishbone`):** Six-dimension root-cause taxonomy (People, Process, Software Code, Database, Testing, Infrastructure).
4. **FMEA Matrix (`/quality/fmea`):** Computes Risk Priority Numbers ($RPN = S \times O \times D$) on a 1–10 scale to prioritize mitigation actions.
5. **SIPOC Process Map (`/quality/sipoc`):** End-to-end operational map connecting Suppliers, Inputs, Process, Outputs, and Customers.
6. **PDCA Continuous Improvement (`/quality/pdca`):** Plan-Do-Check-Act tracker demonstrating verified before-and-after quality improvements.

---

## 10. Academic Attribution

- **Student:** Swati Melkani (CSE - B)
- **Course:** BBAT104 — Fundamentals of Total Quality Management (TQM)
- **Faculty Guide / Department:** Computer Science & Engineering
- **Academic Session:** 2026–27

# Software Requirements Specification (SRS)
## Restaurant Billing System — TQM Q11: Improve Maintainability

**Student:** Swati Melkani  
**Branch & Section:** CSE, Section B  
**Course:** BBAT104 — Fundamentals of Total Quality Management (TQM)  
**Academic Session:** 2026–27  
**Assigned Quality Goal:** Q11 — Improve Maintainability  

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for the **Restaurant Billing System (RBS)**. The system is engineered to satisfy the dual requirements of smooth restaurant point-of-sale billing operations and demonstrable adherence to the Total Quality Management (TQM) quality goal **Q11: Improve Maintainability**.

### 1.2 Scope
The application encompasses:
- Menu catalog management with category filtering and safe deletion guards.
- Point-of-Sale (POS) order creation for Dine-in and Takeaway service types.
- Server-enforced, Decimal-precision financial calculations (Subtotal, Discount, Taxable Amount, Tax, Grand Total).
- Immutable invoice generation protected by database ACID transactions.
- Five mandatory Q11 maintainability features (Modular Structure, Configuration Files, System Settings, Activity Logs, and Code Comments).
- Interactive TQM quality analytics tools (Defect Checksheet, Pareto Analysis, FMEA Risk Prioritization, Fishbone Root-Cause Diagram, SIPOC Process Map, and PDCA Continuous Improvement Register).

---

## 2. User Roles and Personas

| Role | Responsibility | Access Rights |
|------|----------------|---------------|
| **Cashier / POS Operator** | Takes guest orders, modifies cart quantities, applies discounts within configured limits, and prints final invoices. | Order creation, Cart updates, Invoice generation, Menu viewing. |
| **Menu Administrator** | Maintains dishes, updates prices, creates categories, and deactivates unavailable items. | Menu CRUD, Availability toggle. |
| **System Administrator** | Modifies operational policies (taxes, discounts, restaurant branding, logging parameters) and reviews audit logs. | System Settings (`/settings`), Activity Logs (`/logs`). |
| **Quality Analyst (TQM)** | Analyzes billing failures, conducts Pareto and FMEA evaluations, monitors PDCA improvement cycles. | Quality Hub (`/quality`), Defect Checksheet, Pareto, FMEA, Fishbone, SIPOC, PDCA. |

---

## 3. Functional Requirements

### 3.1 Module A: Dashboard
- **FR-D1:** Display live total sales revenue calculated from actual database invoices for the current calendar day.
- **FR-D2:** Display count of finalized bills and active draft orders.
- **FR-D3:** Render dynamic Chart.js visualizations for 7-day sales trends and top 5 ordered dishes.
- **FR-D4:** Present a live indicator of unresolved software defects for immediate quality awareness.

### 3.2 Module B: Menu Management
- **FR-M1:** Support full CRUD operations for menu items with fields: `item_code`, `name`, `category`, `description`, `unit_price`, and `is_available`.
- **FR-M2:** Server-side validation must reject negative prices and blank dish names.
- **FR-M3:** Enforce uniqueness preventing duplicate dish names within the same category.
- **FR-M4:** Safe Deletion Guard: Block permanent deletion of any dish referenced in past order records; mandate deactivation instead.

### 3.3 Module C: Order Management
- **FR-O1:** Create orders supporting `Dine-in` (with table assignment) and `Takeaway` workflows.
- **FR-O2:** Support adding multiple items, adjusting quantities ($>0$), and removing items from open Draft orders.
- **FR-O3:** Snapshot unit prices into `order_items` at order time to preserve historical integrity.
- **FR-O4:** Reject additions of items marked `is_available = 0`.
- **FR-O5:** Enforce order lifecycle states: `Draft -> Finalized` or `Draft -> Cancelled`. Block modifications once an order is Finalized.

### 3.4 Module D: Billing & Invoice Generation
- **FR-B1:** Perform calculations strictly in Python's Decimal format using the sequence:
  $$\text{Subtotal} = \sum (\text{Qty} \times \text{Unit Price})$$
  $$\text{Discount Amount} = \text{Subtotal} \times \frac{\text{Discount Rate}}{100}$$
  $$\text{Taxable Amount} = \text{Subtotal} - \text{Discount Amount}$$
  $$\text{Tax Amount} = \text{Taxable Amount} \times \frac{\text{Tax Rate}}{100}$$
  $$\text{Grand Total} = \text{Taxable Amount} + \text{Tax Amount}$$
- **FR-B2:** Server-side validation must reject discounts exceeding the configured maximum limit (default: 25%).
- **FR-B3:** Finalization must execute within an ACID database transaction.
- **FR-B4:** Generate a sequential, unique invoice number (e.g. `INV-2026-0001`).
- **FR-B5:** Provide an optimized, printer-friendly tax invoice view.

### 3.5 Module E: System Settings (Q11 Feature 3)
- **FR-S1:** Store administrative parameters in the `system_settings` table.
- **FR-S2:** Enable UI updates for Restaurant Profile, Tax Rates, Maximum Discounts, Rounding Rules, Page Sizes, and Log Levels without code edits.
- **FR-S3:** Validate inputs prior to saving and record an audit log entry for every modification.

### 3.6 Module F: Activity Logs (Q11 Feature 4)
- **FR-L1:** Log all business events (Order creation, Item additions, Finalizations, Settings changes) into SQLite `activity_logs`.
- **FR-L2:** Automatically redact sensitive credentials (passwords, tokens, card numbers) from log payloads.
- **FR-L3:** Provide filterable search by module, outcome (Success, Warning, Failure), and date.

### 3.7 Module G: TQM Quality Tools
- **FR-Q1:** Defect Checksheet: Log defects through states `Reported -> Investigating -> Fix Implemented -> Verified -> Closed`.
- **FR-Q2:** Defect Export: Export defect register to downloadable CSV.
- **FR-Q3:** Pareto Analysis: Compute category frequencies and cumulative percentages to separate vital few defects from trivial many.
- **FR-Q4:** FMEA Register: Compute Risk Priority Number ($RPN = \text{Severity} \times \text{Occurrence} \times \text{Detection}$) on a 1–10 scale.
- **FR-Q5:** Ishikawa Fishbone: Classify defect root causes across People, Process, Software Code, Database, Testing, and Infrastructure.
- **FR-Q6:** PDCA Register: Track Plan, Do, Check, and Act cycles with quantitative before-and-after retest evidence.

---

## 4. Non-Functional Requirements

- **Maintainability (Q11):** High modularity separating routes, services, database operations, and templates. Centralized configuration in `.env` and `app/config.py`.
- **Reliability & Consistency:** SQLite database transactions with foreign keys enabled (`PRAGMA foreign_keys = ON;`) ensuring zero orphan records.
- **Precision:** Decimal arithmetic eliminating IEEE-754 floating-point inaccuracies.
- **Usability & Accessibility:** Clean emerald-green responsive interface based on Bootstrap 5; readable across desktop, tablet, and mobile browsers.
- **Performance:** Instantaneous local response time ($< 100\text{ms}$) utilizing database indexes on searchable fields.
- **Security:** Sanitized logs, parameterized SQL queries preventing SQL injection, and server-side validation on all form inputs.

---

## 5. Acceptance Criteria

1. All 28 automated pytest test cases pass cleanly without errors.
2. The application starts locally via `python run.py` on default port 5000.
3. Menu items can be created, edited, deactivated, and filtered.
4. Orders calculate line totals and grand totals matching Decimal formulas.
5. Invoices generate unique sequential numbers and are printable.
6. System settings modified in the UI persist and apply immediately.
7. Defect checksheet, Pareto chart, FMEA table, and PDCA cycles render live data without errors.

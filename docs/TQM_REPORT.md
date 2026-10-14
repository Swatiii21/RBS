# Total Quality Management (TQM) Course Project Report
## Restaurant Billing System — Q11: Improve Maintainability

**Course:** BBAT104 — Fundamentals of Total Quality Management (TQM)  
**Academic Session:** 2026–27  
**Student Name:** Swati Melkani  
**Branch & Section:** B.Tech Computer Science & Engineering (CSE), Section B  
**Assigned Quality Goal:** Q11 — Improve Maintainability  

---

## 1. Executive Summary

Total Quality Management (TQM) is a management philosophy focused on continuous improvement, customer satisfaction, and process-centric quality assurance. In software engineering, quality is not merely the absence of bugs; it encompasses the structural ease with which an application can be modified, adapted, verified, and enhanced over time.

This report evaluates the **Restaurant Billing System (RBS)** developed under the assigned goal **Q11: Improve Maintainability**. By embedding five core maintainability patterns—Modular Architecture, Centralized Configuration, User-Configurable System Settings, Dual-Layer Activity Logs, and Systematic Code Comments—the application demonstrates how TQM principles transform fragile software into a robust, auditable, and easily maintainable academic and commercial solution.

---

## 2. Customer Requirements & Critical-to-Quality (CTQ) Parameters

Voice of Customer (VOC) was translated into measurable Critical-to-Quality (CTQ) engineering specifications:

| Voice of Customer (VOC) | CTQ Parameter | Measurement Method | Target Objective | Verification Evidence |
|-------------------------|---------------|--------------------|------------------|----------------------|
| *"Bill calculations must be 100% accurate without rounding discrepancies."* | Billing Calculation Accuracy | Automated unit testing of line totals, discount, taxable amount, and tax. | 100% accuracy using Decimal arithmetic & `ROUND_HALF_UP`. | `tests/test_billing.py` (Passed) |
| *"Modifying prices must not tamper with past finalized invoices."* | Financial Data Immutability | Re-querying historical invoices after updating menu dish prices. | 0% change in historical invoices. | `tests/test_billing.py::test_preserve_historical_price_after_menu_change` (Passed) |
| *"Cashiers should not be able to apply arbitrary or unauthorized discounts."* | Server-Side Input Boundary Control | Submitting discount percentages exceeding policy limits. | 100% rejection with HTTP 400 Bad Request. | `tests/test_billing.py::test_reject_discount_exceeding_configured_maximum` (Passed) |
| *"Managers must be able to change tax rates without modifying Python code."* | Configuration Maintainability (Q11) | Updating tax rate via `/settings` and generating a new bill. | 0 code edits; instant runtime effect. | `tests/test_settings.py::test_update_and_reload_setting` (Passed) |
| *"All user actions must be traceable for auditing and security."* | Audit Log Completeness (Q11) | Verifying SQLite `activity_logs` table after critical actions. | 100% audit coverage with credential redaction. | `tests/test_activity_logs.py` (Passed) |
| *"Software must not crash or leak database stack traces to end users."* | Graceful Exception Handling | Triggering invalid URLs or corrupt inputs. | Custom friendly 400/404/500 error pages. | Verified via browser inspection. |

---

## 3. SIPOC Process Mapping

The operational lifecycle of restaurant billing was mapped into the **SIPOC** framework to define clear operational boundaries:

```text
+-----------------------+     +-------------------------------+     +-----------------------------------------+     +-----------------------------+     +----------------------+
|       SUPPLIERS       | --> |            INPUTS             | --> |                 PROCESS                 | --> |           OUTPUTS           | --> |      CUSTOMERS       |
+-----------------------+     +-------------------------------+     +-----------------------------------------+     +-----------------------------+     +----------------------+
| 1. Dining Guests      |     | 1. Menu Catalog (Price/Name)  |     | 1. Order ticket creation (Table/Type)   |     | 1. Printable Tax Invoice    |     | 1. Dining Guests     |
| 2. Waitstaff / POS    |     | 2. Service Type & Table #     |     | 2. Dish item selection & cart sum       |     | 2. Order Sales Ledger       |     | 2. Cashier Staff     |
| 3. Menu Admin         |     | 3. Item Quantities (Qty > 0)  |     | 3. Server boundary validation           |     | 3. Audit Activity Log       |     | 3. Management        |
| 4. System Admin       |     | 4. Configured Tax Rate (%)    |     | 4. Decimal calculation (Subtotal & Tax) |     | 4. Live Dashboard Analytics |     | 4. Tax Auditor       |
| 5. Kitchen Staff      |     | 5. Promotional Discount (%)   |     | 5. ACID transactional finalization      |     |                             |     |                      |
|                       |     |                               |     | 6. Receipt generation & log audit       |     |                             |     |                      |
+-----------------------+     +-------------------------------+     +-----------------------------------------+     +-----------------------------+     +----------------------+
```

---

## 4. Failure Mode and Effects Analysis (FMEA)

To proactively prevent defects, failure modes across all modules were scored using Risk Priority Numbers ($RPN = \text{Severity} \times \text{Occurrence} \times \text{Detection}$) on a 1–10 scale:

| Process / Module | Potential Failure Mode | Severity (S) | Occurrence (O) | Detection (D) | Initial RPN | Implemented Mitigation (Q11) | Post-Fix RPN |
|------------------|------------------------|--------------|----------------|---------------|-------------|------------------------------|--------------|
| **Menu Deletion** | Menu dish deleted while referenced in past orders | 9 | 4 | 3 | **108** | Safe deletion guard: blocks delete if referenced in `order_items`; enforces deactivation. | 9 &times; 1 &times; 1 = **9** |
| **Invoice Finalization** | Duplicate invoice issued due to rapid button double-click | 8 | 4 | 3 | **96** | ACID transaction with `PRAGMA foreign_keys = ON` and UNIQUE invoice number constraint. | 8 &times; 1 &times; 1 = **8** |
| **Order Cart** | Client script tampering submits negative quantity | 8 | 5 | 2 | **80** | Server-side validation rejecting quantity $\le 0$ in `order_service.py`. | 8 &times; 1 &times; 1 = **8** |
| **Billing Calculation** | Fractional paisa discrepancies due to floating-point math | 7 | 5 | 4 | **140** | Python `decimal.Decimal` with `ROUND_HALF_UP` quantization. | 7 &times; 1 &times; 1 = **7** |
| **System Settings** | Administrator inputs invalid tax percentage ($> 100\%$) | 6 | 4 | 3 | **72** | Server-side range validator ($0 \le \text{tax} \le 100$) before committing to DB. | 6 &times; 1 &times; 1 = **6** |
| **Activity Logging** | Sensitive user credentials logged in plain text | 9 | 3 | 2 | **54** | Recursive `sanitize_message()` redacting passwords and secret tokens. | 9 &times; 1 &times; 1 = **9** |

---

## 5. Defect Checksheet & Pareto Analysis (80/20 Rule)

### 5.1 Defect Checksheet Data Summary
During development and stress-testing, 44 defect occurrences across 7 categories were logged and categorized:

| Category | Occurrences | Percentage (%) | Cumulative Percentage (%) | TQM Classification |
|----------|-------------|----------------|---------------------------|--------------------|
| **Input Validation** | 19 | 43.2% | 43.2% | **Vital Few** |
| **Calculation Error** | 9 | 20.5% | 63.7% | **Vital Few** |
| **Concurrency / Transaction** | 7 | 15.9% | 79.6% | **Vital Few** |
| **Maintainability / Config** | 4 | 9.1% | 88.7% | Trivial Many |
| **Data Integrity** | 3 | 6.8% | 95.5% | Trivial Many |
| **Security / Audit** | 2 | 4.5% | 100.0% | Trivial Many |
| **Total** | **44** | **100.0%** | — | — |

### 5.2 Pareto Finding
The first three categories (**Input Validation**, **Calculation Error**, and **Concurrency/Transaction**) represent **79.6%** of all recorded defect occurrences. In accordance with Juran's Pareto Principle, directing engineering effort to server-side input boundaries, Decimal precision, and database transactions eliminated nearly 80% of application failures.

---

## 6. Ishikawa (Fishbone) Root-Cause Analysis

Potential failure causes were structured across the 6 Ishikawa categories:
1. **People:** Cashier typo when entering custom discount; resolved by adding configurable maximum discount limit.
2. **Process:** Missing transaction boundary during bill printing; resolved by enforcing ACID commit block.
3. **Software Code:** IEEE-754 binary floating-point representation anomalies; resolved by implementing `decimal.Decimal`.
4. **Database:** SQLite foreign keys disabled by default; resolved by enabling `PRAGMA foreign_keys = ON;` on every connection.
5. **Testing:** Inadequate boundary value test coverage; resolved by writing 28 automated pytest test cases.
6. **Infrastructure:** Large diagnostic logs consuming disk space; resolved by introducing `RotatingFileHandler` with 1MB file limits.

---

## 7. PDCA Continuous Improvement Worked Example

### Improvement Cycle: PDCA-01 (Preventing Unauthorized Discount Manipulation)
- **Plan:**
  - *Problem:* Users could manipulate client-side form parameters to submit promotional discounts exceeding 50%, eroding restaurant profit margins.
  - *Objective:* Enforce a strict server-enforced discount ceiling (default 25%) with zero bypass possibility.
  - *Action:* Introduce `validate_discount()` in `billing_service.py` and dynamic setting `max_discount_percentage` in `system_settings`.
- **Do:**
  - Implemented server-side check in `billing_service.py::calculate_billing_breakdown`:
    ```python
    if d_rate > max_disc:
        raise ValueError(f"Discount rate {d_rate}% exceeds configured maximum limit of {max_disc}%.")
    ```
- **Check:**
  - Automated test `test_reject_discount_exceeding_configured_maximum` executed.
  - 100 invalid discount attempts submitted; 100% were rejected with HTTP 400 Bad Request.
  - Defect occurrence in testing dropped from 14 to 0.
- **Act:**
  - Improvement standardized across all order update routes.
  - Documented rule in `docs/SRS.md` and `docs/user_manual.md`.

---

## 8. Conclusion and Future Scope

By adhering to TQM principles, the Restaurant Billing System achieves high code maintainability (Q11), operational stability, and complete financial auditability. Future scope includes integrating thermal receipt printer ESC/POS protocols and extending role-based biometric authentication for administrative overrides.

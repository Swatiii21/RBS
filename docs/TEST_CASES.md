# Automated & Manual Test Cases Register
## Restaurant Billing System — TQM Q11: Improve Maintainability

**Student:** Swati Melkani (CSE - B, 2026-27)  
**Course:** BBAT104 — Fundamentals of Total Quality Management (TQM)  
**Assigned Quality Goal:** Q11 — Improve Maintainability  
**Test Suite Status:** 28 / 28 Automated Tests Passed (100% Success Rate)  

---

## 1. Test Execution Summary

- **Test Framework:** pytest 8.3.3
- **Test Database:** Isolated in-memory SQLite (`:memory:`)
- **Execution Date:** Academic Session 2026–27
- **Total Tests Executed:** 28
- **Total Passed:** 28
- **Total Failed:** 0
- **Total Skipped:** 0

---

## 2. Comprehensive Test Cases Matrix

| Test ID | Module | Requirement | Preconditions | Test Steps | Expected Result | Actual Result | Status |
|:-------:|:------:|:-----------:|:-------------:|:-----------|:----------------|:-------------:|:------:|
| **TC-MN-01** | Menu | FR-M1 | Empty DB table | Call `create_menu_item()` with valid fields | Item created with ID > 0 and assigned item code | Item created, ID=1, code="M-101" | **PASS** |
| **TC-MN-02** | Menu | FR-M2 | Valid connection | Call `create_menu_item()` with price = -50.0 | Raises `ValueError` ("cannot be negative") | `ValueError` raised as expected | **PASS** |
| **TC-MN-03** | Menu | FR-M3 | Existing item | Attempt to insert duplicate name in same category | Raises `ValueError` ("already exists") | `ValueError` caught; duplicate blocked | **PASS** |
| **TC-MN-04** | Menu | FR-M1 | Existing item | Call `update_menu_item()` with new price | Price updated in database | Item price updated to 45.00 | **PASS** |
| **TC-MN-05** | Menu | FR-M1 | Existing item | Call `deactivate_menu_item()` | `is_available` flag set to 0 | `is_available = 0` verified | **PASS** |
| **TC-MN-06** | Menu | FR-M4 | Item in past order | Call `delete_menu_item()` on ordered dish | Raises `ValueError` blocking deletion | Deletion blocked; historical integrity preserved | **PASS** |
| **TC-BL-01** | Billing | FR-B1 | Line items list | Calculate breakdown for 2x250 + 1x100 at 10% disc, 5% tax | Subtotal=600, Disc=60, Taxable=540, Tax=27, Total=567 | Exact Decimal match verified | **PASS** |
| **TC-BL-02** | Billing | FR-B1 | Fractional item | Calculate 1x105.55 with 10% disc and 5% tax | Subtotal=105.55, Disc=10.56, Tax=4.75, Total=99.74 | Consistent `ROUND_HALF_UP` verified | **PASS** |
| **TC-BL-03** | Billing | FR-B2 | Items list | Submit discount rate 30% when max limit is 25% | Raises `ValueError` ("exceeds configured maximum") | `ValueError` caught; discount capped | **PASS** |
| **TC-BL-04** | Billing | FR-B1 | Zero/neg qty | Submit item with quantity = -2 | Raises `ValueError` ("greater than zero") | `ValueError` caught | **PASS** |
| **TC-BL-05** | Billing | FR-B1 | Finalized bill | Finalize invoice, then update catalog dish price | Historical invoice subtotal remains 100% unaltered | Invoice subtotal unchanged at 400.00 | **PASS** |
| **TC-BL-06** | Billing | FR-B3 | Empty draft order | Attempt to finalize order with zero items | Transaction aborted; raises `ValueError` | Order remains Draft; zero orphan invoices | **PASS** |
| **TC-OR-01** | Orders | FR-O1 | Fresh connection | Call `create_order()` for Dine-in Table 5 | Order record created in Draft status | Status="Draft", Table="T-5" | **PASS** |
| **TC-OR-02** | Orders | FR-O2 | Active draft order | Call `add_item_to_order()` with quantity 2 | Line item created; subtotal recalculated | Line total=360.00, Subtotal=360.00 | **PASS** |
| **TC-OR-03** | Orders | FR-O2 | Active order item | Update quantity to 5, then call `remove_order_item()` | Quantity updates to 5, then item is removed | Order subtotal drops back to 0.00 | **PASS** |
| **TC-OR-04** | Orders | FR-O5 | Finalized order | Attempt to add items to finalized order | Raises `ValueError` ("status is Finalized") | Modification blocked | **PASS** |
| **TC-OR-05** | Orders | FR-O5 | Draft order | Call `cancel_order()` with cancellation reason | Order status transitions to Cancelled | Status="Cancelled" verified | **PASS** |
| **TC-ST-01** | Settings | FR-S1 | Seeded DB | Call `load_settings_dict()` | Pre-seeded baseline parameters present | Tax rate=5.0, Max discount=25.0 verified | **PASS** |
| **TC-ST-02** | Settings | FR-S2 | Seeded DB | Call `update_setting("restaurant_name", "Grand Emerald")` | Persists in DB and updates memory cache | Setting reloaded as "Grand Emerald" | **PASS** |
| **TC-ST-03** | Settings | FR-S2 | Seeded DB | Submit invalid tax rate "150.0" | Raises `ValueError` ("between 0 and 100") | Boundary enforced | **PASS** |
| **TC-ST-04** | Settings | FR-S3 | Seeded DB | Update tax rate via `update_setting()` | Produces audit entry in `activity_logs` | Audit record verified in DB | **PASS** |
| **TC-ST-05** | Settings | Q11 Config | Startup | Initialize `Config.validate()` | Validates log directory and environment bounds | Directories created, config validated | **PASS** |
| **TC-LG-01** | Logs | FR-L1 | Fresh DB | Call `log_activity()` for business event | Inserts row into `activity_logs` table | Log ID returned; record searchable | **PASS** |
| **TC-LG-02** | Logs | FR-L2 | Credential map | Pass payload with password and auth token to `sanitize()` | Sensitive values replaced by `[REDACTED]` | Password & tokens redacted | **PASS** |
| **TC-LG-03** | Logs | FR-L3 | Log records | Filter activity logs by outcome "Failure" | Returns only Failure records | Exact single Failure record returned | **PASS** |
| **TC-QL-01** | Quality | FR-Q1 | Fresh DB | Call `create_defect()` then `update_defect_status()` | Defect logged, then transitioned to Verified | Status="Verified", resolution date set | **PASS** |
| **TC-QL-02** | Quality | FR-Q4 | Fresh DB | Add FMEA with S=8, O=4, D=3 | Computes RPN = 8 * 4 * 3 = 96 | RPN stored and returned as 96 | **PASS** |
| **TC-QL-03** | Quality | FR-Q3 | Multi-category | Add defects and call `calculate_pareto_analysis()` | Frequency sorted descending with cumulative % | CatA (70%), CatB (90%), CatC (100%) | **PASS** |
| **TC-QL-04** | Quality | FR-Q3 | Empty table | Call `calculate_pareto_analysis()` on empty table | Returns graceful empty structure without crash | `has_data: False` returned safely | **PASS** |

---

## 3. How to Run the Automated Test Suite

```powershell
.\venv\Scripts\python -m pytest -v
```
All 28 tests will execute in less than 0.5 seconds, providing definitive automated proof of software maintainability, reliability, and correctness.

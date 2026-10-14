# Failure Mode and Effects Analysis (FMEA) Register
## Restaurant Billing System — TQM Q11: Improve Maintainability

**Student:** Swati Melkani (CSE - B, 2026-27)  
**Course:** BBAT104 — Fundamentals of Total Quality Management (TQM)  
**Assigned Quality Goal:** Q11 — Improve Maintainability  

---

## 1. FMEA Rating Scale Definitions

Each potential failure mode is evaluated across three parameters scored from 1 (lowest risk) to 10 (highest risk):

### 1.1 Severity Rating (S)
| Score | Classification | Description |
|:-----:|----------------|-------------|
| **9–10** | **Catastrophic / Hazardous** | Financial record corruption, permanent data loss, regulatory tax penalty, or crash. |
| **7–8** | **Major** | Customer overcharged/undercharged, duplicate billing, incorrect tax totals. |
| **5–6** | **Moderate** | Feature unavailable, system requires server reboot to apply settings. |
| **3–4** | **Minor** | Cosmetic display defect, minor latency in query loading. |
| **1–2** | **Negligible** | Typographical error in label; zero impact on financial calculations. |

### 1.2 Occurrence Rating (O)
| Score | Classification | Failure Probability |
|:-----:|----------------|---------------------|
| **9–10** | **Very High** | Defect occurs almost constantly on every interaction without prevention. |
| **7–8** | **High** | Defect occurs frequently during regular peak-hour operations. |
| **5–6** | **Moderate** | Defect occurs occasionally under specific edge cases. |
| **3–4** | **Low** | Defect occurs rarely in normal usage. |
| **1–2** | **Remote** | Failure is virtually impossible under normal conditions. |

### 1.3 Detection Rating (D)
| Score | Classification | Detectability Prior to User Exposure |
|:-----:|----------------|--------------------------------------|
| **9–10** | **Almost Impossible** | Defect produces silent financial drift with zero detection mechanism. |
| **7–8** | **Poor** | Defect is detected only when a guest complains about the receipt. |
| **5–6** | **Moderate** | Defect is detected by an end-of-day accountant or auditor. |
| **3–4** | **High** | Defect is caught automatically by server-side validation or audit logs. |
| **1–2** | **Almost Certain** | Defect is immediately caught by automated unit tests during build. |

$$\mathbf{RPN} = \mathbf{Severity} \times \mathbf{Occurrence} \times \mathbf{Detection} \quad (1 \le \text{RPN} \le 1000)$$

---

## 2. FMEA Evaluation Matrix

| ID | Subsystem / Process | Potential Failure Mode | Potential Effect | Potential Cause | Existing Controls | S | O | D | RPN | Recommended Mitigation | Status |
|----|---------------------|------------------------|------------------|-----------------|-------------------|:-:|:-:|:-:|:---:|------------------------|:------:|
| **FM-01** | Billing Calculation | Fractional paisa discrepancies in tax amount | Customer undercharged or overcharged; auditing non-compliance | Floating-point IEEE-754 binary math | Client-side JS script | 7 | 5 | 4 | **140** | Replace floating point with Python `decimal.Decimal` and `ROUND_HALF_UP` quantization. | **Mitigated** |
| **FM-02** | Menu Deletion | Deleting a dish breaks foreign key links in historical receipts | Financial ledger queries crash or return null records | Absence of safe deletion guards in service | Standard SQLite delete | 9 | 4 | 3 | **108** | Restrict delete operation in `menu_service.py` if item has order history; mandate deactivation. | **Mitigated** |
| **FM-03** | Invoice Finalization | Duplicate invoice issued when staff rapidly double-clicks Finalize | Two invoices for same order; financial confusion | Lack of transaction isolation & idempotency | Standard HTTP POST | 8 | 4 | 3 | **96** | ACID transaction with `BEGIN IMMEDIATE` and UNIQUE constraint on invoice numbers. | **Mitigated** |
| **FM-04** | Order Management | Submitting negative quantity or price | Negative bill totals resulting in cash revenue leakage | Reliance on HTML5 form attributes alone | HTML input `min="1"` | 8 | 5 | 2 | **80** | Server-side boundary checks rejecting quantity $\le 0$ and price $< 0$ in service layer. | **Mitigated** |
| **FM-05** | System Settings | Administrator inputs invalid tax percentage ($> 100\%$) | System generates nonsensical invoices | Unvalidated settings form inputs | None | 6 | 4 | 3 | **72** | Server-side validation range ($0 \le \text{tax} \le 100$) before committing updates. | **Mitigated** |
| **FM-06** | Activity Logging | Clear-text passwords written to log files | Security and privacy compliance breach | Unsanitized logging of request dictionaries | None | 9 | 3 | 2 | **54** | Recursive `sanitize_message()` redacting sensitive keywords (`password`, `token`, etc.). | **Mitigated** |
| **FM-07** | Configuration | Database connection failure when instance directory missing | Application startup crash on fresh computer | Missing directory creation before connection | None | 6 | 3 | 2 | **36** | `Config.validate()` automatically creates `instance/` and `logs/` directories upon startup. | **Mitigated** |

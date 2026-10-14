# User Manual & Operator Guide
## Restaurant Billing System — TQM Q11: Improve Maintainability

**Student:** Swati Melkani (CSE - B, 2026-27)  
**Course:** BBAT104 — Fundamentals of Total Quality Management (TQM)  
**Assigned Quality Goal:** Q11 — Improve Maintainability  

---

## 1. Quick Start Guide

### 1.1 Launching the Application
1. Open Windows PowerShell in the project directory:
   ```powershell
   cd c:\Users\HP\Downloads\RBS
   ```
2. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Run the application:
   ```powershell
   python run.py
   ```
4. Open your browser and navigate to: **`http://127.0.0.1:5000/`**

---

## 2. Navigating the Modules

### 2.1 Operational Dashboard (`/` or `/dashboard`)
- **Top Metric Cards:** Monitor today's revenue, bills issued, active open tickets, and total menu dishes.
- **Sales Trend:** Interactive chart showing daily sales volume over the past 7 days.
- **Top Dishes:** Doughnut chart highlighting the most frequently ordered items.
- **Quick Links:** One-click shortcuts to take orders, add dishes, or review quality logs.

### 2.2 Menu Catalog Management (`/menu`)
- **Add Dish:** Click **"+ Add New Item"**, specify dish name, category, unit price, and optional description.
- **Filter Dishes:** Search by dish name or filter by category (Starters, Main Course, Breads, Beverages, Desserts).
- **Toggle Availability:** Click the slash/check icon to mark items unavailable when ingredients run out. Unavailable items are hidden from POS order entry but preserved in historical bills.
- **Safe Delete:** Deleting an item is safely blocked if that dish has been ordered in historical bills.

### 2.3 Order Management & POS (`/orders`)
- **Create Order Ticket:** Click **"New Order Ticket"**, select service type (`Dine-in` with Table #, or `Takeaway`), and input customer details.
- **Add Dishes to Ticket:** Select dishes from the dropdown and specify the quantity. The system snapshots the price and recalculates the subtotal and tax instantly.
- **Adjust Quantities:** Change quantity numbers directly in the cart table or click the delete button to remove a dish.
- **Promotional Discount:** Enter a discount percentage. The server enforces the configured maximum discount ceiling (default 25%) and rejects invalid values.
- **Finalize Bill:** Click **"Finalize Bill & Issue Invoice"**. The system executes an ACID transaction, locks the ticket, generates a unique invoice number, and directs you to the printable receipt.

### 2.4 Printable Tax Invoice (`/billing/invoice/<invoice_number>`)
- Displays restaurant branding, customer details, itemized breakdown, tax policy, and grand total.
- Click **"Print Invoice"** to trigger browser print styling (automatically hides navigation bars and buttons for clean paper printouts).

### 2.5 Billing History (`/billing/history`)
- Search by customer name, order number, or invoice code.
- Filter by date range (From Date to To Date) and status (`Active`, `Cancelled`, `Corrected`).

### 2.6 System Settings (`/settings`) — *Q11 Feature 3*
- **Restaurant Profile:** Edit restaurant name, address, phone number, and receipt footer text.
- **Billing Settings:** Adjust applicable tax rate (e.g. 5%), maximum discount allowance, currency symbol, and rounding policy (`ROUND_HALF_UP`).
- **Application Settings:** Set default table pagination limit and date/time formatting.
- Click **"Save System Settings"** to persist updates immediately without needing to restart the server.

### 2.7 Activity Logs (`/logs`) — *Q11 Feature 4*
- Review the immutable audit trail of all business actions (menu creation, order edits, bill finalizations, setting updates).
- Filter by subsystem module or outcome (`Success`, `Warning`, `Failure`).

---

## 3. TQM Quality Analytics Tools

### 3.1 Defect Checksheet (`/quality/defects`)
- Log observed errors with module, description, category, severity, occurrence count, and Ishikawa root-cause.
- Progress defects through lifecycle stages: `Reported -> Investigating -> Fix Implemented -> Verified -> Closed`.
- Download the complete defect register as a CSV file via **"Export CSV Register"**.

### 3.2 Pareto Analysis (`/quality/pareto`)
- View dual-axis Pareto chart displaying defect frequency bars alongside the cumulative percentage line.
- The 80% threshold separates the "Vital Few" defects requiring immediate engineering attention from the "Trivial Many".

### 3.3 FMEA Risk Prioritization (`/quality/fmea`)
- Review Risk Priority Numbers ($RPN = \text{Severity} \times \text{Occurrence} \times \text{Detection}$) scored from 1 to 10.
- High-risk items ($RPN \ge 90$) are automatically highlighted for prioritized mitigation.

### 3.4 Ishikawa / Fishbone Diagram (`/quality/fishbone`)
- Inspect root causes across 6 categories: People, Process, Software Code, Database, Testing, and Infrastructure.

### 3.5 SIPOC Process Map (`/quality/sipoc`)
- Review the end-to-end process flow from Suppliers and Inputs to Process Steps, Outputs, and Customers.

### 3.6 PDCA Continuous Improvement (`/quality/pdca`)
- Track structured Plan-Do-Check-Act cycles with verified before-and-after retest evidence.

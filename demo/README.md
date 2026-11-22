# Chitragupta — Demonstration Guide for Hackathon Judges

**Chitragupta** is an intelligent back-office web application designed specifically for one-person micro-businesses (freelancers, agencies, tutors, shopkeepers, boutique clinics). It solves Problem Statement 1: The One-Person Back Office by tracking who owes money, automating follow-ups, and forecasting whether cash reserves will last 30 to 90 days.

---

## 1. Quick Start Commands

The application is configured to run on fixed ports:
- **Frontend**: http://127.0.0.1:5180
- **Backend API**: http://127.0.0.1:8010

### Running the Backend
From the root `Chitragupta` folder in PowerShell:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

### Running the Frontend
From the root `Chitragupta` folder in a second terminal:
```powershell
cd frontend
npm run dev
```

### Automated Backend Tests
Run the comprehensive 82-test suite:
```powershell
.\backend\.venv\Scripts\python.exe -m pytest tests/backend -o pythonpath=backend
```

---

## 2. Evaluation Walkthrough (Scenarios A through E)

### Scenario A: Customer → Invoice → Partial Payment Workflow
1. Navigate to **Customers** (`/customers`) and click **Add Customer**. Create a new client (e.g., "Matrix Cloud Systems").
2. Navigate to **Invoices** (`/invoices`) and click **New Invoice**. Assign it to the customer, enter line items, tax percentage, and save as draft.
3. On the Invoice Details page, click **Mark as Sent**.
4. Click **Record Payment** (`/payments/new`) or use the button on the invoice page. Record a partial payment (e.g., 50% via UPI).
5. Open the **Dashboard** (`/`) to observe real-time recalculation of Total Outstanding, Total Collected, and Ageing Buckets.

### Scenario B: Overdue Detection & Assisted Reminders
1. Open the **Reminders** screen (`/reminders`).
2. Notice the queue classified into 5 distinct urgency tiers:
   - Upcoming payment due (next 1–5 days)
   - Payment due today
   - First overdue reminder (1–7 days overdue)
   - Follow-up overdue reminder (8–21 days overdue)
   - Final polite payment follow-up (>21 days overdue)
3. Click the **WhatsApp**, **Email**, or **SMS** button on any overdue invoice (e.g. `INV-0004` Apex Learning Academy).
4. Review the personalized template pre-filled with the customer name, amount due, and UPI ID / Bank coordinates.
5. Edit the message if desired, click **Copy Message**, or test **Open in WhatsApp** / **Open Mail Client**.
6. Click **Mark as Reminded** to record the follow-up in the immutable audit log.

### Scenario C: Scheduled Business Expenses & Cash Burn
1. Navigate to **Cash Flow** (`/cash-flow`).
2. Review the scheduled monthly outflows (Office Rent, Cloud SaaS, Assistant Stipend, Utilities).
3. Click **Add Outflow** to record an upcoming one-off or recurring expense (e.g., "Tax Advance ₹25,000" due in 6 days).
4. Watch the projected cash balance dip on the exact due date in the Recharts visualization.

### Scenario D: What-If Simulation for Delayed Payments
1. On the **Cash Flow** screen (`/cash-flow`), locate the **Interactive Scenario Simulator**:
   *"What happens if my major customer pays 15 days late?"*
2. Select a customer (e.g., "TechNova Solutions Pvt Ltd" or "Apex Learning Academy") or a specific invoice.
3. Click **+15 Days** or **+30 Days**.
4. Notice how the purple simulated trajectory shifts rightward relative to the baseline blue curve.
5. Check the **Simulation Impact Analysis**: if the delayed cash causes reserves to dip below the ₹50,000 safety threshold, a high-priority shortage warning is displayed, listing the specific expenses affected during the shortage window.

### Scenario E: Business Settings Persistence & Reset
1. Navigate to **Settings** (`/settings`).
2. Modify business details, UPI ID, or default payment terms. Click **Save Settings**.
3. Refresh the page: observe that all settings persist via SQLite.
4. Need a fresh demonstration state? Click **Reset & Re-seed Demo Data** to restore the standard hackathon benchmark dataset.

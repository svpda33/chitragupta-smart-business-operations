# Chitragupta — Final Judge Demonstration Script (2–3 Minutes)

**Hackathon:** ACE Builders Hackathon 2026 — Problem Statement 1: *The One-Person Back Office*  
**Live Local URLs:** Frontend `http://127.0.0.1:5180` | Backend API `http://127.0.0.1:8010`  
**Disclaimer:** All business names, customer contacts, invoices, payments, and expenses shown are 100% synthetic demonstration data.

---

## Alignment with Official Judging Criteria

| Criterion | Weight | How Chitragupta Demonstrates It |
|---|---|---|
| **Working Product** | 30% | Live full-stack React + FastAPI + SQLite app with real persistence, integer-paise financial math, 82 automated backend tests, and zero mock metrics. |
| **Business Viability** | 25% | Solves the #1 survival problem for India's solo freelancers, clinics, tutors, and micro-agencies: cash-flow visibility and overdue collection without hiring an accountant. |
| **Problem / User Clarity** | 20% | Answers three daily owner questions in seconds: *Who owes me? Who should I chase today? Will cash last the next 30–90 days?* |
| **Build Quality** | 15% | Clean layered architecture (Routes $\rightarrow$ Services $\rightarrow$ Models), immutable audit trails, non-destructive what-if simulations, decimal-safe currency handling. |
| **Presentation** | 10% | Crisp 2.5-minute narrative following a solo consultant's real Monday morning workflow. |

---

## Synthetic Demo Persona

- **Business:** *Chitragupta Operations Consulting* (Owner: *Aditi Sharma*, Bengaluru)
- **Current Snapshot:** 6 clients, 10 invoices (paid, partially paid, pending, overdue, and draft), 4 payments (including 1 reversed bounced cheque for audit demo), and 5 scheduled expenses (rent, SaaS, assistant stipend, internet, and upcoming UPS maintenance).

---

## 2.5-Minute Live Demo Script & Exact Browser Sequence

### 1. The Morning Pulse — Financial Dashboard (`0:00 – 0:35`)
- **Navigate to:** `http://127.0.0.1:5180/` (Dashboard)
- **Say:** *"Meet Aditi, a solo operations consultant. Instead of juggling spreadsheets and WhatsApp chats on Monday morning, she opens Chitragupta."*
- **Point out:**
  - **KPI Cards:** ₹3,28,160 outstanding, ₹1,79,360 overdue across 3 invoices, ₹4,28,600 estimated cash on hand, and ~197 days of cash runway.
  - **Actionable Alerts:** Immediately highlights *Apex Learning Academy* (`INV-0004`, ₹84,960, 28 days overdue) and upcoming *Hardware UPS* expense.
  - **Visualizations:** Receivables Ageing Breakdown bar chart and Invoice Pipeline donut chart.

### 2. Invoice Creation & Partial Payment Tracking (`0:35 – 1:10`)
- **Navigate via Sidebar:** **Invoices** (`/invoices`) $\rightarrow$ click **INV-0003** (*Zenith Retail & Supermarket*) or click **New Invoice** (`/invoices/new`).
- **Demonstrate:**
  - Show how invoices calculate GST in exact integer paise, transition `draft` $\rightarrow$ `sent`, and lock amounts once payments are recorded.
  - Click **Record Payment** (`/payments/new`) — show how overpayment is blocked and partial payments immediately recalculate the outstanding balance and dashboard totals.
  - Visit **Payments** (`/payments`) to show full payment history, transaction references (UPI/NEFT/IMPS), and the reversed bounced cheque with its immutable audit reason.

### 3. Assisted Overdue Reminders (`1:10 – 1:40`)
- **Navigate via Sidebar:** **Reminders** (`/reminders`)
- **Say:** *"Chasing late payers is awkward and time-consuming. Chitragupta prioritizes who to follow up with today across 5 urgency tiers — from upcoming reminders to final polite follow-ups."*
- **Demonstrate:**
  - Click **WhatsApp** on **INV-0004** (*Apex Learning Academy*, 28 days overdue).
  - Show the pre-filled, editable message containing the exact balance, due date, and Aditi's UPI ID / bank details from Settings.
  - Highlight 1-click **Copy Message**, **Open in WhatsApp**, and **Mark as Reminded** (which logs the follow-up to the audit trail without claiming fake automated sending).

### 4. 30–90-Day Cash-Flow Forecasting & "15-Day Late Payment" What-If (`1:40 – 2:20`)
- **Navigate via Sidebar:** **Cash Flow** (`/cash-flow`)
- **Demonstrate:**
  - Toggle **30 / 60 / 90 Days** to show expected customer inflows minus scheduled rent, payroll, and utility outflows against the safety reserve line.
  - **Run the signature What-If:** Under **Interactive Scenario Simulator**, select **Apex Learning Academy** (or **TechNova Solutions**) and click **+15 Days** (or **+30 Days**).
  - Show the purple simulated curve diverging from the blue baseline curve, the **Simulation Impact Analysis** explanation, and which scheduled expenses are exposed if reserves dip — while emphasizing that **zero actual invoices or payments are modified**.

### 5. Business Settings & Persistence (`2:20 – 2:40`)
- **Navigate via Sidebar:** **Settings** (`/settings`)
- **Demonstrate:** Show business profile, UPI/bank details, default payment terms, cash reserve parameters, and the confirmation-gated **Reset & Re-seed Demo Data** button for reproducible judging.

---

## Honest Limitations & Next Roadmap

- **Messaging Dispatch:** Uses an honest copy-and-launch workflow (`wa.me` / `mailto:`) rather than claiming automated server-side WhatsApp/SMS delivery (which requires paid third-party gateway credentials).
- **Single Currency & Single User:** Built for an INR one-person back office; multi-currency and multi-user RBAC are planned post-MVP.
- **Cloud Persistence:** Local MVP runs on SQLite; production cloud hosting uses PostgreSQL (documented in `docs/deployment.md`).

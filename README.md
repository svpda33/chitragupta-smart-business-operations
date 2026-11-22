# Chitragupta — Smart Business Operations

Chitragupta is an AI-powered business operations and financial management platform for small businesses. It combines invoicing, payments, inventory, cash-flow forecasting, business analytics, and an AI Finance Copilot.

> All demo business profiles and records are synthetic and fictional.

## Problem Statement

Small and one-person businesses often track customers, invoices, inventory, receivables, and expenses in disconnected spreadsheets or manual records. Chitragupta provides one workspace for everyday financial operations and practical next-step guidance.

## Main Features

- Financial dashboard with receivables, collections, cash, runway, ageing, pipeline, activity, and alerts
- Customer management and multi-line GST invoices
- Partial/full payments, overpayment prevention, references, and reversals
- Product catalogue, stock levels, inventory valuation, low-stock states, and stock movements
- 30/60/90-day cash-flow forecasts and delayed-payment what-if simulations
- Priority reminders with WhatsApp, email, and SMS-ready drafts
- Business settings, scheduled expenses, notes, onboarding, and isolated business workspaces
- Gemini-powered AI Finance Copilot grounded in signed-in business data

## Technology Stack

- **Frontend:** React 18, Vite, React Router, Tailwind CSS, Recharts, Axios
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy
- **Database:** SQLite for local use
- **AI:** Google Gemini through the `google-genai` Python SDK
- **Testing:** pytest and Vitest

## System Architecture

The React/Vite frontend communicates with FastAPI under `/api`. Authenticated routes resolve the current user's primary business, and SQLAlchemy service modules perform database and financial operations scoped by `business_id`. The AI copilot uses a fixed set of read-only backend tools to retrieve verified ledger and inventory figures.

## Installation and Local Setup

### Prerequisites

- Windows PowerShell
- Python 3.11 or newer
- Node.js and npm

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Set `GEMINI_API_KEY` in `backend/.env` only. A placeholder value is included in [backend/.env.example](backend/.env.example); never commit `backend/.env`.

### 2. Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5180`. Backend API documentation is available at `http://127.0.0.1:8010/docs`.

Optional frontend configuration is documented in [frontend/.env.example](frontend/.env.example). The default API base is `/api`.

### 3. Tests

From the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest tests/backend -o pythonpath=backend
cd frontend
npm test
npm run build
```

## Demo Accounts – Try Chitragupta

Two preconfigured business accounts have already been created. Evaluators can sign in immediately without registering or setting up a business.

### Account 1: Urban Stationery & Office Supplies

- **Owner:** Rahul Sharma
- **Email:** `demo@chitragupta.in`
- **Password:** `ChitraDemo@2026!`
- **Sample data:** 50 products

### Account 2: Oakwood Furniture Studio

- **Owner:** Arjun Mehta
- **Email:** `furniture.demo@chitragupta.in`
- **Password:** `FurnitureDemo@2026!`
- **Sample data:** 50 products

Both accounts have separate business data, including products, customers, invoices, payments, expenses, inventory, and notes, according to the actual implementation.

These credentials are public demonstration credentials for hackathon evaluation only. Each business has isolated data, and evaluators can log in using either account to explore the application. Normal users can register their own independent business account.

See [docs/DEMO_ACCOUNT.md](docs/DEMO_ACCOUNT.md) for the complete demo information.

## AI Finance Copilot

The copilot answers finance and inventory questions using whitelisted read-only tools. It presents actual ledger figures, cash-flow estimates, and what-if simulations separately. It does not send reminders, change ledger records, or expose Gemini credentials. A Gemini API key and network access are required for live model responses.

# Application Dashboard

Chitragupta provides a unified financial and operational overview for small businesses.

| Light Mode | Dark Mode |
|---|---|
| ![Chitragupta dashboard in light mode](docs/screenshots/dashboard-light.png) | ![Chitragupta dashboard in dark mode](docs/screenshots/dashboard-dark.png) |

## Project Documentation

- [Architecture](docs/architecture.md)
- [API documentation](docs/api-documentation.md)
- [Business logic](docs/business-logic.md)
- [Deployment guide](docs/deployment.md)
- [Demo account and seeded data](docs/DEMO_ACCOUNT.md)

## Important Limitations

- Reminders use copy-and-launch workflows rather than claiming automated server-side WhatsApp/SMS delivery.
- Local development uses SQLite. Production deployments should use managed persistent storage and backups.
- Additional hardening, team roles, monitoring, and operational controls would be required for production use.
- Live AI answers require a valid Gemini API key and network access.

## Future Improvements

- Add approved-provider reminder delivery
- Add managed PostgreSQL and backup/restore tooling
- Extend role-based team access
- Add reporting exports and accounting integrations

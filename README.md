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

## Application Screenshots

These 1440 × 900 desktop screenshots show the actual application with synthetic demonstration data.

### Application Overview

Landing and authentication screens for evaluators.

| Landing — Light | Landing — Dark |
|---|---|
| ![Chitragupta landing page in light mode](docs/screenshots/landing-light.png) | ![Chitragupta landing page in dark mode](docs/screenshots/landing-dark.png) |

| Login — Light | Login — Dark |
|---|---|
| ![Chitragupta login in light mode](docs/screenshots/login-light.png) | ![Chitragupta login in dark mode](docs/screenshots/login-dark.png) |

| Registration — Light | Registration — Dark |
|---|---|
| ![Chitragupta registration in light mode](docs/screenshots/registration-light.png) | ![Chitragupta registration in dark mode](docs/screenshots/registration-dark.png) |

### Dashboard

Live KPIs, receivables, collection activity, charts, stock alerts, and actionable business insights.

| Dashboard — Light | Dashboard — Dark |
|---|---|
| ![Financial dashboard in light mode](docs/screenshots/dashboard-light.png) | ![Financial dashboard in dark mode](docs/screenshots/dashboard-dark.png) |

### AI Finance Copilot

Ledger-grounded financial summaries and actionable questions from the AI assistant.

| AI Copilot — Light | AI Copilot — Dark |
|---|---|
| ![AI Finance Copilot in light mode](docs/screenshots/ai-finance-copilot-light.png) | ![AI Finance Copilot in dark mode](docs/screenshots/ai-finance-copilot-dark.png) |

### Cash Flow & Forecasting

Cash projections, scheduled outflows, runway estimates, and delayed-payment what-if simulations.

| Cash Flow — Light | Cash Flow — Dark |
|---|---|
| ![Cash flow forecast in light mode](docs/screenshots/cash-flow-light.png) | ![Cash flow forecast in dark mode](docs/screenshots/cash-flow-dark.png) |

### Customer Management

Customer records, searchable accounts, and individual business relationships.

| Customers — Light | Customers — Dark |
|---|---|
| ![Customer management in light mode](docs/screenshots/customers-light.png) | ![Customer management in dark mode](docs/screenshots/customers-dark.png) |

### Invoice Management

Invoice lists, payment status, lifecycle details, and GST-ready invoice creation.

| Invoices — Light | Invoices — Dark |
|---|---|
| ![Invoice list in light mode](docs/screenshots/invoices-light.png) | ![Invoice list in dark mode](docs/screenshots/invoices-dark.png) |

| Invoice Creation — Light | Invoice Creation — Dark |
|---|---|
| ![Invoice creation in light mode](docs/screenshots/invoice-creation-light.png) | ![Invoice creation in dark mode](docs/screenshots/invoice-creation-dark.png) |

### Payment Management

Payment records, methods, references, outstanding balances, and transaction history.

| Payments — Light | Payments — Dark |
|---|---|
| ![Payment management in light mode](docs/screenshots/payments-light.png) | ![Payment management in dark mode](docs/screenshots/payments-dark.png) |

### Reminders

Overdue and upcoming payment follow-ups with ready-to-use reminder actions.

| Reminders — Light | Reminders — Dark |
|---|---|
| ![Payment reminders in light mode](docs/screenshots/reminders-light.png) | ![Payment reminders in dark mode](docs/screenshots/reminders-dark.png) |

### Product Catalogue & Inventory

Demo products, categories, stock levels, valuation, and low/out-of-stock alerts.

| Catalogue — Light | Catalogue — Dark |
|---|---|
| ![Product catalogue in light mode](docs/screenshots/catalogue-light.png) | ![Product catalogue in dark mode](docs/screenshots/catalogue-dark.png) |

| Inventory — Light | Inventory — Dark |
|---|---|
| ![Inventory in light mode](docs/screenshots/inventory-light.png) | ![Inventory in dark mode](docs/screenshots/inventory-dark.png) |

### Business Notepad

Operational notes for customers, suppliers, finance, and daily tasks.

| Notepad — Light | Notepad — Dark |
|---|---|
| ![Business notepad in light mode](docs/screenshots/notepad-light.png) | ![Business notepad in dark mode](docs/screenshots/notepad-dark.png) |

### Settings & Themes

Business profile configuration and consistent light/dark theme controls.

| Settings — Light | Settings — Dark |
|---|---|
| ![Business settings in light mode](docs/screenshots/settings-light.png) | ![Business settings in dark mode](docs/screenshots/settings-dark.png) |

### Authentication and Demo Business

Evaluators can select either preconfigured public demo account from the login screen.

| Oakwood Dashboard — Light | Oakwood Dashboard — Dark |
|---|---|
| ![Oakwood demonstration dashboard in light mode](docs/screenshots/oakwood-dashboard-light.png) | ![Oakwood demonstration dashboard in dark mode](docs/screenshots/oakwood-dashboard-dark.png) |

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

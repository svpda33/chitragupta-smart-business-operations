# Architecture

## Overview

Chitragupta is a single-user web application that runs on one machine during the hackathon. A React frontend talks to a FastAPI backend over REST. The backend stores data in SQLite through SQLAlchemy.

## Frontend responsibilities

- Render pages and components for the nine MVP features.
- Hold only view state. All financial figures come from the backend.
- Send requests through `frontend/src/services/`.
- Display forecasts with a clear "Forecast" label, separate from actual balances.

## Backend responsibilities

- Validate requests and responses with Pydantic schemas.
- Expose REST endpoints under `/api`.
- Apply business rules in `app/services/`: outstanding balance, overdue status, ageing buckets, cash-flow forecast, what-if scenarios and alerts.
- Never write to the database when computing a scenario.

## Database responsibilities

- SQLite file stored at a path set by configuration.
- Tables: business settings, customers, invoices, payments, recurring bills, follow-up log, alert dismissals.
- Monetary values stored as integer paise. Dates stored as calendar dates.
- Access only through SQLAlchemy models and sessions. No raw SQL outside the database layer.
- Schema kept portable so that PostgreSQL can be adopted later without changing business logic.

## Data flow

1. The user acts in a React page.
2. The page calls a function in `services/`.
3. The request reaches a FastAPI route, which validates it with a schema.
4. The route calls a backend service, which reads or writes through a model.
5. The service returns a result, and the route returns a response schema.
6. The page renders the response.

## Separation of actual and forecast data

- Actual figures (balances, overdue totals, cash on hand) come only from recorded invoices, payments and bills.
- Forecast figures (projected daily cash, what-if results) are computed on request and never persisted.

## Out of scope for the MVP

Authentication, multi-user access, bank or payment-gateway integration, automatic message sending, deployment to a hosted environment.

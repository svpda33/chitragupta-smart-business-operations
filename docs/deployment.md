# Chitragupta — Production Deployment Guide

This guide covers deploying **Chitragupta** (React + Vite frontend and FastAPI + SQLAlchemy backend) to public cloud hosting without losing data or exposing secrets.

---

## 1. Environment Variables

### Backend (`backend/.env`)
Copy [backend/.env.example](../backend/.env.example) and configure for production:

```env
APP_ENV=production
# IMPORTANT: Do NOT use local SQLite on ephemeral cloud filesystems (Render free tier, Fly ephemeral, Railway without volume).
# Use a managed PostgreSQL database or a persistent volume for SQLite:
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/chitragupta
DEFAULT_CURRENCY=INR
HIGH_OVERDUE_THRESHOLD_PAISE=5000000
CORS_ORIGINS=https://your-chitragupta-frontend.vercel.app
```

> **Storage Warning:** Cloud PaaS containers reset their local filesystem on redeploy or sleep. SQLite (`sqlite:///./instance/chitragupta.db`) is safe only for local development or when mounted on a **persistent disk/volume**. For production, provision managed PostgreSQL (e.g., Render Postgres, Supabase, Neon, or Railway Postgres) and set `DATABASE_URL` accordingly.

### Frontend (`frontend/.env.production`)
Copy [frontend/.env.example](../frontend/.env.example) and point to your deployed backend API:

```env
VITE_API_BASE_URL=https://your-chitragupta-api.onrender.com/api
```

---

## 2. Backend Deployment (Render / Railway / Fly.io)

- **Root Directory:** `backend`
- **Build Command:**
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command (binds to `0.0.0.0` and platform `$PORT`):**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8010}
  ```
- **Health Check Path:** `/api/health`

---

## 3. Frontend Deployment (Vercel / Netlify / Cloudflare Pages)

- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variable:** `VITE_API_BASE_URL=https://<your-backend-host>/api`
- **SPA Routing Rewrite:** Ensure all non-file routes rewrite to `/index.html` so direct URLs and page refreshes on `/customers`, `/invoices/:id`, `/cash-flow`, etc. work without 404 errors:
  - **Vercel:** Create `frontend/vercel.json` with `{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }`.
  - **Netlify:** Add `/* /index.html 200` to `frontend/public/_redirects`.

---

## 4. Pre-Deployment Security Checklist

- [ ] `.env` files are never committed (already ignored in `.gitignore`).
- [ ] Local SQLite files (`*.db`, `instance/`) are ignored in `.gitignore`.
- [ ] `CORS_ORIGINS` is restricted to the exact deployed frontend origin(s).
- [ ] Only synthetic demonstration data is seeded on public demo instances (`POST /api/demo/seed`).

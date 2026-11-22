from fastapi import APIRouter

from app.api.routes import (
    ai,
    auth,
    cashflow,
    customers,
    dashboard,
    demo,
    expenses,
    health,
    invoices,
    notes,
    payments,
    products,
    reminders,
    settings,
    uploads,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(expenses.router)
api_router.include_router(settings.router)
api_router.include_router(dashboard.router)
api_router.include_router(cashflow.router)
api_router.include_router(reminders.router)
api_router.include_router(notes.router)
api_router.include_router(uploads.router)
api_router.include_router(demo.router)
api_router.include_router(ai.router)

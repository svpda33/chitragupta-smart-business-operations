# Chitragupta Business Logic (Phase 2)

This file describes the rules implemented in the backend services. Routes only parse and return data; the rules live in `app/services`.

## Money

- Every amount in the database is an integer number of paise.
- Requests accept rupees as a JSON number or a string. The value is parsed with `Decimal`. More than 2 decimals, or a non-numeric value, is rejected with a 422 field error. The value is converted exactly to paise (no float rounding).
- Responses use integer fields ending in `_paise`. Messages show rupees with two decimals and thousands separators, e.g. `₹2,655.59`.

## Invoice totals

For each item: `line_total = quantity x unit_price_paise`.

- `subtotal = sum of line totals`
- `tax = (subtotal x tax_percent + 50) // 100` (round half up to the nearest paisa)
- `total = subtotal + tax`

Worked example: lines 2 x 1000.00 and 1 x 250.50, tax 18%.
- line totals 200000 and 25050, subtotal 225050
- tax = (225050 x 18 + 50) // 100 = 40509
- total 265559 (₹2,655.59)

Limits: 1 to 50 items; quantity 1 to 100000; unit price greater than 0; tax 0 to 100%; total at most 1,000,000,000 paise.

## Invoice lifecycle and derived status

Stored lifecycle: `draft` (created) then `sent` (after the send action). Only drafts can be sent and only drafts can be deleted. A sent invoice is part of the payment record and is never deleted.

Derived status (computed on read, never stored), with `outstanding = total - active paid` and `today` = the server date:

1. lifecycle `draft` -> `draft`, days overdue 0.
2. outstanding is 0 or less -> `paid`.
3. due date before today -> `overdue`, days overdue = today - due date (in days).
4. otherwise, nothing paid -> `pending`; some paid -> `partially_paid`.

An invoice due today is not overdue. Overdue days are 0 when not overdue.

## Payments

- Payments can only be recorded against `sent` invoices.
- Amount must be greater than 0. Payment date defaults to today and cannot be in the future.
- Method must be one of `cash`, `bank_transfer`, `upi`, `other`.
- Overpayment is refused: `already active paid + new amount` must not exceed the invoice total. The 422 message states the remaining balance.
- Only **active** payments count towards paid totals.
- A payment is never deleted. Reversal marks it `reversed` and stores `reversed_at` and a reason of 3 to 300 characters. A reversed payment cannot be reversed again (409) or edited (409).
- Editing an active payment re-checks the overpayment limit, excluding that payment itself. The audit entry lists the changed fields (for example `amount ₹1,000.00 -> ₹1,200.00`).

## Changing invoices after payment

- If an invoice has at least one active payment, changes to customer, invoice date, due date, tax percent, items or total are refused with 409. The user must reverse payments first.
- Description, notes and invoice number can still be changed. Invoice numbers must stay unique.
- Without active payments, a draft or sent invoice can be edited in full.

## Customers

- Name is required (1 to 120 characters) and must be unique, ignoring case.
- Email must match a basic address pattern and be at most 254 characters. Phone must have 7 to 15 digits after spaces, dashes and brackets are removed, with an optional leading `+`.
- Empty optional text is stored as null.
- **Delete rule:** a customer with any invoice (draft or sent) cannot be deleted (409). The record is kept to preserve payment history.
- Customer summaries: invoice count includes drafts; money totals use non-draft invoices and active payments; overdue is the outstanding balance of overdue invoices.

## Audit history

- Each create, update, send, payment record, payment edit and payment reversal writes an audit event.
- Invoice events: `created`, `updated`, `sent`, `payment_recorded`, `payment_updated`, `payment_reversed`.
- Payment events: `payment_recorded`, `payment_updated`, `payment_reversed`.
- Events are returned newest first. Audit rows are not edited or deleted by the application.
- Deleting a draft removes the invoice row; its audit rows remain in the table.

## Invoice numbers

- Generated numbers have the form `INV-0001`, `INV-0002`, ... (next after the highest existing `INV-n`).
- A supplied number is trimmed, must be 1 to 32 characters and must be unique.

## Migration note

- The application creates tables at startup with `Base.metadata.create_all`. It creates tables that do not exist yet and never drops or alters existing tables or data.
- `create_all` does **not** add new columns to an existing table. If a column is added to a model later, a migration (for example Alembic) is required before the change can be used against an existing database file.
- New tables introduced in Phase 2 (customers, invoices, invoice_items, payments, audit_events) are created on first start; existing data is not touched.

## Not in this phase

- Forecasting, reminders and dashboard totals are intentionally not implemented.

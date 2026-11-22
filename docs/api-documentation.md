# Chitragupta API Documentation (Phase 2)

Base URL: `http://127.0.0.1:8010/api` (backend port 8010).

All money values are integers in **paise** (1 rupee = 100 paise). Request money fields accept rupees as a JSON number or string with at most 2 decimals (for example `1250.5`, `"1250.50"`). Dates use ISO format `YYYY-MM-DD`.

## Error format

Every error response is JSON.

```json
{ "detail": "Customer not found." }
```

When the error belongs to one input field, an `errors` list is added:

```json
{
  "detail": "A customer with this name already exists.",
  "errors": [{ "field": "name", "message": "A customer with this name already exists." }]
}
```

Validation errors (HTTP 422) use a fixed headline and one entry per field:

```json
{
  "detail": "Please correct the highlighted fields.",
  "errors": [{ "field": "items.0.unit_price", "message": "Enter an amount in rupees with at most 2 decimal places, for example 1250.50." }]
}
```

Unexpected server errors return HTTP 500 with `{"detail": "An unexpected error occurred."}`.

## List format

List endpoints return:

```json
{ "items": [], "total": 0, "page": 1, "page_size": 20 }
```

`page` defaults to 1 (minimum 1). `page_size` defaults to 20 (minimum 1, maximum 100). `total` is the number of matching rows before pagination.

## Health (existing)

### GET /api/health
- Success: 200 `{status, app, environment, database, version}`.

## Customers

### GET /api/customers
- Query: `search` (optional, matches name, email or phone, case-insensitive), `page`, `page_size`.
- Ordered by name.
- Success: 200, list format with items of CustomerOut.
- Errors: 422 (`page_size` above 100, `page` below 1).

### POST /api/customers
- Body:
  - `name` (string, required, 1 to 120 characters after trimming)
  - `email` (string or null; must be a valid address, max 254)
  - `phone` (string or null; 7 to 15 digits, optional leading `+`; spaces, dashes and brackets are ignored; the trimmed input is stored; max 20 characters)
  - `address` (string or null, max 500)
  - `notes` (string or null, max 1000)
- Empty strings become null.
- Success: 201, CustomerOut.
- Errors: 409 duplicate name (case-insensitive) with `errors[0].field = "name"`; 422 invalid email or phone.

### GET /api/customers/{customer_id}
- Success: 200, CustomerOut.
- Errors: 404 `"Customer not found."`.

### PUT /api/customers/{customer_id}
- Full replacement of the editable fields (same body as POST).
- Success: 200, CustomerOut.
- Errors: 404, 409 duplicate name (own name is allowed), 422.

### DELETE /api/customers/{customer_id}
- Success: 204, no body.
- Errors: 404; 409 `"This customer has invoices and cannot be deleted. Keep the record to preserve payment history."` when any invoice (draft or sent) exists.

**CustomerOut**: `id, name, email, phone, address, notes, created_at, updated_at, invoice_count, total_invoiced_paise, total_paid_paise, outstanding_paise, overdue_paise`.
- `invoice_count`: all invoices including drafts.
- `total_invoiced_paise`: sum of totals of non-draft invoices.
- `total_paid_paise`: sum of active payments.
- `outstanding_paise`: per non-draft invoice `total - active paid`, summed.
- `overdue_paise`: outstanding of non-draft invoices whose derived status is `overdue`.

## Invoices

Invoice statuses (derived, not stored): `draft`, `pending`, `partially_paid`, `overdue`, `paid`. The stored lifecycle is `draft` or `sent`.

### GET /api/invoices
- Query: `search` (matches invoice number, description or customer name), `status` (one of `draft|pending|partially_paid|overdue|paid`), `customer_id`, `page`, `page_size`.
- Ordered by invoice date (newest first), then id (newest first). Filtering by status happens after the status is derived; pagination happens after filtering.
- Success: 200, list format with items of InvoiceListItem.
- Errors: 422 (unknown status, bad paging).

### POST /api/invoices
- Body:
  - `customer_id` (int, required)
  - `invoice_number` (string or null, max 32). Blank or omitted means the next number `INV-0001`, `INV-0002`, ... is generated.
  - `invoice_date` (date, required)
  - `due_date` (date, required; must not be before `invoice_date`)
  - `description` (string, 1 to 200)
  - `notes` (string or null, max 1000)
  - `tax_percent` (int, 0 to 100, default 0)
  - `items` (list, 1 to 50 entries), each: `description` (1 to 200), `quantity` (int, 1 to 100000), `unit_price` (rupees, greater than 0)
- Success: 201, InvoiceOut (created as `draft`).
- Errors: 404 `"Customer not found."`; 409 `"An invoice with this number already exists."` (field `invoice_number`); 422 with field `due_date`, `items`, `quantity`, `unit_price`, `tax_percent` or `invoice_number`.

### GET /api/invoices/{invoice_id}
- Success: 200, InvoiceOut.
- Errors: 404 `"Invoice not found."`.

### PUT /api/invoices/{invoice_id}
- Same body as POST. `invoice_number` omitted or blank keeps the current number.
- Description and notes can always be changed.
- If the invoice has any **active** payment, changing customer, dates, tax, items or total is refused.
- Success: 200, InvoiceOut.
- Errors: 404; 409 `"This invoice has payments recorded. Reverse the payments before changing its amounts."`; 409 `"An invoice with this number already exists."`; 422 as for POST.

### POST /api/invoices/{invoice_id}/send
- Moves a draft to `sent` and sets `sent_at`. No body.
- Success: 200, InvoiceOut.
- Errors: 404; 409 `"Only draft invoices can be sent."`.

### DELETE /api/invoices/{invoice_id}
- Only drafts can be deleted.
- Success: 204, no body.
- Errors: 404; 409 `"Only draft invoices can be deleted. Sent invoices are part of the payment record."`.

**InvoiceListItem**: `id, invoice_number, customer_id, customer_name, description, invoice_date, due_date, lifecycle, status, total_paise, paid_paise, outstanding_paise, days_overdue`.

**InvoiceOut** adds: `notes, tax_percent, subtotal_paise, tax_paise, sent_at, items, payments, history`.
- `items`: `id, position, description, quantity, unit_price_paise, line_total_paise`.
- `payments`: PaymentOut list (includes reversed payments, ordered by payment date then id).
- `history`: HistoryEvent list (invoice events and its payments' events, newest first).

**HistoryEvent**: `id, action, summary, created_at`.

## Payments

### GET /api/payments
- Query: `invoice_id`, `customer_id`, `status` (`active|reversed`), `page`, `page_size`.
- Ordered by payment date (newest first), then id (newest first).
- Success: 200, list format with items of PaymentOut.

### POST /api/payments
- Body:
  - `invoice_id` (int, required)
  - `amount` (rupees, greater than 0)
  - `payment_date` (date, optional, default today; must not be in the future)
  - `method` (one of `cash`, `bank_transfer`, `upi`, `other`)
  - `reference` (string or null, max 100)
  - `notes` (string or null, max 500)
- The invoice must be `sent`.
- Success: 201, PaymentDetail.
- Errors: 404 `"Invoice not found."`; 409 `"Payments can only be recorded against sent invoices."`; 422 with field `amount` when the payment exceeds the outstanding balance (message gives the balance, e.g. `"The payment is more than the outstanding balance of ₹2,655.59."`), field `payment_date`, or field `method`.

### GET /api/payments/{payment_id}
- Success: 200, PaymentDetail. Errors: 404 `"Payment not found."`.

### PUT /api/payments/{payment_id}
- Body: `amount, payment_date (required), method, reference, notes` (same rules as POST).
- Active payments only.
- Success: 200, PaymentDetail.
- Errors: 404; 409 `"Reversed payments cannot be edited."`; 422 (overpayment re-checked, excluding this payment).

### POST /api/payments/{payment_id}/reverse
- Body: `{ "reason": "..." }`, reason 3 to 300 characters after trimming.
- The payment row is kept; status becomes `reversed`.
- Success: 200, PaymentDetail.
- Errors: 404; 409 `"This payment has already been reversed."`; 422 field `reason`.

**PaymentOut**: `id, invoice_id, invoice_number, customer_id, customer_name, amount_paise, payment_date, method, reference, notes, status, reversed_at, reversal_reason, created_at`.
**PaymentDetail** = PaymentOut + `history`.

## Route summary

| Method | Path | Success |
|---|---|---|
| GET | /api/health | 200 |
| GET | /api/customers | 200 |
| POST | /api/customers | 201 |
| GET | /api/customers/{customer_id} | 200 |
| PUT | /api/customers/{customer_id} | 200 |
| DELETE | /api/customers/{customer_id} | 204 |
| GET | /api/invoices | 200 |
| POST | /api/invoices | 201 |
| GET | /api/invoices/{invoice_id} | 200 |
| PUT | /api/invoices/{invoice_id} | 200 |
| POST | /api/invoices/{invoice_id}/send | 200 |
| DELETE | /api/invoices/{invoice_id} | 204 |
| GET | /api/payments | 200 |
| POST | /api/payments | 201 |
| GET | /api/payments/{payment_id} | 200 |
| PUT | /api/payments/{payment_id} | 200 |
| POST | /api/payments/{payment_id}/reverse | 200 |

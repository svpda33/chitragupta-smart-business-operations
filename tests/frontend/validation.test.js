import { describe, it, expect } from "vitest";
import {
  validateCustomerForm,
  validateInvoiceForm,
  validatePaymentForm,
} from "../../frontend/src/utils/validation.js";

function pad(value) {
  return String(value).padStart(2, "0");
}

function tomorrowIso() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

const validInvoice = {
  customer_id: 1,
  invoice_number: "INV-001",
  invoice_date: "2026-03-01",
  due_date: "2026-03-15",
  description: "Monthly bookkeeping",
  tax_percent: 18,
  items: [{ description: "Bookkeeping", quantity: 2, unit_price: "500.00" }],
};

const validPayment = {
  invoice_id: 1,
  amount: "100",
  payment_date: "2026-03-01",
  method: "upi",
};

describe("validateCustomerForm", () => {
  it("requires a name", () => {
    expect(validateCustomerForm({ name: "  " }).name).toBe("Name is required.");
  });

  it("flags an invalid email", () => {
    const errors = validateCustomerForm({ name: "Asha", email: "bad" });
    expect(errors.email).toBe("Enter a valid email address.");
  });

  it("flags an invalid phone number", () => {
    const errors = validateCustomerForm({ name: "Asha", phone: "12ab" });
    expect(errors.phone).toBe("Enter a valid phone number, for example +91 98765 43210.");
  });

  it("accepts a phone number with spaces", () => {
    const errors = validateCustomerForm({ name: "Asha", phone: "+91 98765 43210" });
    expect(errors.phone).toBeUndefined();
  });
});

describe("validateInvoiceForm", () => {
  it("returns no errors for a valid invoice", () => {
    expect(validateInvoiceForm(validInvoice)).toEqual({});
  });

  it("flags a due date before the invoice date", () => {
    const errors = validateInvoiceForm({ ...validInvoice, due_date: "2026-02-28" });
    expect(errors).toHaveProperty("due_date");
  });

  it("requires at least one line item", () => {
    const errors = validateInvoiceForm({ ...validInvoice, items: [] });
    expect(errors).toHaveProperty("items");
  });

  it("flags a zero quantity on the line item", () => {
    const items = [{ description: "Bookkeeping", quantity: 0, unit_price: "500" }];
    const errors = validateInvoiceForm({ ...validInvoice, items });
    expect(errors).toHaveProperty("items.0.quantity");
  });
});

describe("validatePaymentForm", () => {
  it("returns no errors for a valid payment", () => {
    expect(validatePaymentForm(validPayment, 50000)).toEqual({});
  });

  it("flags an amount above the outstanding balance", () => {
    const errors = validatePaymentForm({ ...validPayment, amount: "600" }, 50000);
    expect(errors).toHaveProperty("amount");
    expect(errors.amount).toBe("Amount is more than the outstanding balance of ₹500.00");
  });

  it("flags a payment date in the future", () => {
    const errors = validatePaymentForm({ ...validPayment, payment_date: tomorrowIso() }, 50000);
    expect(errors).toHaveProperty("payment_date");
    expect(errors.payment_date).toBe("Payment date cannot be in the future.");
  });
});

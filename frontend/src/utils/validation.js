import { paiseToRupeeInput, rupeeStringToPaise, validateRupeeInput } from "./money.js";
import { isBeforeIso, todayIso } from "./dates.js";

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PHONE_PATTERN = /^\+?[0-9]{7,15}$/;

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}

function isBlank(value) {
  return value === undefined || value === null || String(value).trim() === "";
}

export function validateCustomerForm(values = {}) {
  const errors = {};

  const name = text(values.name);
  if (name === "") {
    errors.name = "Name is required.";
  } else if (name.length > 120) {
    errors.name = "Name must be at most 120 characters.";
  }

  const email = text(values.email);
  if (email !== "" && (email.length > 254 || !EMAIL_PATTERN.test(email))) {
    errors.email = "Enter a valid email address.";
  }

  const phone = text(values.phone);
  if (phone !== "") {
    const normalised = phone.replace(/[\s\-()]/g, "");
    if (!PHONE_PATTERN.test(normalised)) {
      errors.phone = "Enter a valid phone number, for example +91 98765 43210.";
    }
  }

  return errors;
}

export function validateInvoiceForm(values = {}) {
  const errors = {};

  if (isBlank(values.customer_id)) {
    errors.customer_id = "Choose a customer.";
  }

  if (text(values.invoice_number).length > 32) {
    errors.invoice_number = "Invoice number must be at most 32 characters.";
  }

  if (isBlank(values.invoice_date)) {
    errors.invoice_date = "Invoice date is required.";
  }

  if (isBlank(values.due_date)) {
    errors.due_date = "Due date is required.";
  } else if (isBeforeIso(values.due_date, values.invoice_date)) {
    errors.due_date = "Due date cannot be before the invoice date.";
  }

  const description = text(values.description);
  if (description === "") {
    errors.description = "Description is required.";
  } else if (description.length > 200) {
    errors.description = "Description must be at most 200 characters.";
  }

  const taxText = String(values.tax_percent ?? "").trim();
  const tax = /^\d{1,3}$/.test(taxText) ? Number(taxText) : NaN;
  if (!(tax >= 0 && tax <= 100)) {
    errors.tax_percent = "Tax must be a whole number from 0 to 100.";
  }

  const items = Array.isArray(values.items) ? values.items : [];
  if (items.length < 1) {
    errors.items = "Add at least one line item.";
  }

  items.forEach((item, index) => {
    const line = item ?? {};

    if (text(line.description) === "") {
      errors[`items.${index}.description`] = "Description is required.";
    }

    const quantityText = String(line.quantity ?? "").trim();
    const quantity = /^\d+$/.test(quantityText) ? Number(quantityText) : NaN;
    if (!(quantity >= 1 && quantity <= 100000)) {
      errors[`items.${index}.quantity`] = "Quantity must be a whole number of at least 1.";
    }

    const priceError = validateRupeeInput(line.unit_price, { allowZero: false });
    if (priceError) {
      errors[`items.${index}.unit_price`] = priceError;
    }
  });

  return errors;
}

export function validatePaymentForm(values = {}, outstandingPaise) {
  const errors = {};

  if (isBlank(values.invoice_id)) {
    errors.invoice_id = "Choose an invoice.";
  }

  const amountError = validateRupeeInput(values.amount);
  if (amountError) {
    errors.amount = amountError;
  } else if (rupeeStringToPaise(values.amount) > outstandingPaise) {
    errors.amount = `Amount is more than the outstanding balance of ₹${paiseToRupeeInput(outstandingPaise)}`;
  }

  if (isBlank(values.payment_date)) {
    errors.payment_date = "Payment date is required.";
  } else if (isBeforeIso(todayIso(), values.payment_date)) {
    errors.payment_date = "Payment date cannot be in the future.";
  }

  if (isBlank(values.method)) {
    errors.method = "Choose a payment method.";
  }

  return errors;
}

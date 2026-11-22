import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  FileCheck2,
  FileText,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react";
import PageHeader from "../components/common/PageHeader.jsx";
import Button from "../components/common/Button.jsx";
import Input from "../components/common/Input.jsx";
import Textarea from "../components/common/Textarea.jsx";
import Select from "../components/common/Select.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "../context/ToastContext.jsx";
import { getInvoice, createInvoice, updateInvoice } from "../services/invoiceService.js";
import { listCustomers } from "../services/customerService.js";
import { listProducts } from "../services/productService.js";
import { getSettings } from "../services/settingsService.js";
import { formatDate, todayIso } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";
import { paiseToRupeeInput, rupeeStringToPaise, validateRupeeInput } from "../utils/money.js";
import { validateInvoiceForm } from "../utils/validation.js";

const CARD =
  "rounded-2xl border border-slate-200 bg-white shadow-2xs dark:border-slate-800 dark:bg-[#111827]";
const PRIMARY_LINK =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700";

const TAX_PATTERN = /^\d{1,3}$/;
const QUANTITY_PATTERN = /^\d+$/;
const TOP_LEVEL_FIELDS = [
  "customer_id",
  "invoice_number",
  "invoice_date",
  "due_date",
  "description",
  "notes",
  "tax_percent",
  "items",
];
const LINE_FIELD_PATTERN = /^items\.\d+\.(description|quantity|unit_price)$/;

const STEPS = [
  { id: 1, title: "Client & Dates", subtitle: "Who & when" },
  { id: 2, title: "Items & GST", subtitle: "Scope & pricing" },
  { id: 3, title: "Review & Issue", subtitle: "Notes & generate" },
];

let lineKeySequence = 0;

function createLine(seed = {}) {
  lineKeySequence += 1;
  return {
    key: `line-${lineKeySequence}`,
    product_id: null,
    description: "",
    quantity: "1",
    unit_price: "",
    ...seed,
  };
}

function addDaysIso(baseIso, days) {
  const [y, m, d] = String(baseIso || todayIso()).split("-").map(Number);
  const dt = new Date(Date.UTC(y, (m || 1) - 1, (d || 1) + days));
  return dt.toISOString().slice(0, 10);
}

function parseQuantity(text) {
  const trimmed = String(text ?? "").trim();
  return QUANTITY_PATTERN.test(trimmed) ? Number(trimmed) : NaN;
}

function parseTaxPercent(text) {
  const trimmed = String(text ?? "").trim();
  if (!TAX_PATTERN.test(trimmed)) return null;
  const value = Number(trimmed);
  return value >= 0 && value <= 100 ? value : null;
}

function lineTotalPaise(line) {
  const quantity = parseQuantity(line.quantity);
  if (!(quantity >= 1 && quantity <= 100000)) return null;
  if (validateRupeeInput(line.unit_price)) return null;
  return quantity * rupeeStringToPaise(line.unit_price);
}

function pick(errors, keys) {
  const result = {};
  keys.forEach((key) => {
    if (errors[key]) result[key] = errors[key];
  });
  return result;
}

function withoutKey(errors, key) {
  if (!(key in errors)) return errors;
  const next = { ...errors };
  delete next[key];
  return next;
}

function withoutItemErrors(errors) {
  return Object.fromEntries(Object.entries(errors).filter(([key]) => !key.startsWith("items")));
}

function isKnownErrorKey(key) {
  return TOP_LEVEL_FIELDS.includes(key) || LINE_FIELD_PATTERN.test(key);
}

export default function InvoiceFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const showToast = useToast();

  const presetParam = searchParams.get("customerId") ?? "";
  const presetCustomerId = /^\d+$/.test(presetParam) ? presetParam : "";

  const customersState = useAsync(() => listCustomers({ page_size: 100 }), []);
  const productsState = useAsync(() => listProducts({ active_only: true }), []);
  const settingsState = useAsync(getSettings, []);
  const invoiceState = useAsync(
    () => (isEdit ? getInvoice(id) : Promise.resolve(null)),
    [id, isEdit]
  );

  const customers = customersState.data?.items ?? [];
  const catalogue = Array.isArray(productsState.data) ? productsState.data : [];
  const businessSettings = settingsState.data;
  const invoice = invoiceState.data;
  const locked =
    isEdit && Boolean(invoice) && (invoice.payments ?? []).some((p) => p.status === "active");

  const [step, setStep] = useState(1);
  const [values, setValues] = useState(() => ({
    customer_id: presetCustomerId,
    invoice_number: "",
    invoice_date: todayIso(),
    due_date: addDaysIso(todayIso(), 15),
    description: "",
    notes: "",
    tax_percent: "18",
  }));
  const [lines, setLines] = useState(() => [createLine()]);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [generatedInvoice, setGeneratedInvoice] = useState(null);

  // Apply business defaults on new invoice when settings load
  useEffect(() => {
    if (isEdit || !businessSettings) return;
    setValues((cur) => ({
      ...cur,
      tax_percent:
        cur.tax_percent === "18"
          ? String(businessSettings.default_tax_percent ?? 18)
          : cur.tax_percent,
      due_date: addDaysIso(
        cur.invoice_date || todayIso(),
        businessSettings.default_payment_terms_days ?? 15
      ),
    }));
  }, [businessSettings, isEdit]);

  // Pre-fill in edit mode
  useEffect(() => {
    if (!invoice) return;
    setValues({
      customer_id: String(invoice.customer_id),
      invoice_number: invoice.invoice_number ?? "",
      invoice_date: invoice.invoice_date ?? "",
      due_date: invoice.due_date ?? "",
      description: invoice.description ?? "",
      notes: invoice.notes ?? "",
      tax_percent: String(invoice.tax_percent ?? 0),
    });
    setLines(
      invoice.items.length > 0
        ? invoice.items.map((item) =>
            createLine({
              product_id: item.product_id ?? null,
              description: item.description,
              quantity: String(item.quantity),
              unit_price: paiseToRupeeInput(item.unit_price_paise),
            })
          )
        : [createLine()]
    );
    setErrors({});
  }, [invoice]);

  const heading = isEdit ? "Edit Invoice" : "Invoice Studio";
  const header = (
    <PageHeader
      title={heading}
      description={
        isEdit
          ? "Update invoice details with live document preview."
          : "Build a GST-ready invoice step by step with live animated preview."
      }
      actions={
        <Link
          to={isEdit ? `/invoices/${id}` : "/invoices"}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
      }
    />
  );

  if (invoiceState.error) {
    return (
      <div className="space-y-6">
        {header}
        <ErrorState message={invoiceState.error.message} onRetry={invoiceState.refresh} />
      </div>
    );
  }
  if (customersState.error) {
    return (
      <div className="space-y-6">
        {header}
        <ErrorState message={customersState.error.message} onRetry={customersState.refresh} />
      </div>
    );
  }
  if (!customersState.data || (isEdit && !invoice)) {
    return (
      <div className="space-y-6">
        {header}
        <LoadingState />
      </div>
    );
  }
  if (customers.length === 0) {
    return (
      <div className="space-y-6">
        {header}
        <EmptyState
          icon={FileText}
          title="Add a customer first"
          message="Every invoice belongs to a customer."
          action={
            <Link to="/customers/new" className={PRIMARY_LINK}>
              Add customer
            </Link>
          }
        />
      </div>
    );
  }

  function setField(name, value) {
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => withoutKey(current, name));
  }

  function setLineField(index, field, value) {
    setLines((current) =>
      current.map((line, i) => (i === index ? { ...line, [field]: value } : line))
    );
    setErrors((current) => withoutKey(current, `items.${index}.${field}`));
  }

  function addLine() {
    setLines((current) => [...current, createLine()]);
  }

  function removeLine(index) {
    setLines((current) => (current.length > 1 ? current.filter((_, i) => i !== index) : current));
    setErrors((current) => withoutItemErrors(current));
  }

  const selectedCustomer = customers.find((c) => String(c.id) === String(values.customer_id));
  const lineTotals = lines.map(lineTotalPaise);
  const subtotalPaise = lineTotals.reduce((sum, paise) => sum + (paise ?? 0), 0);
  const taxPercent = parseTaxPercent(values.tax_percent);
  const taxPaise = taxPercent === null ? null : Math.floor((subtotalPaise * taxPercent + 50) / 100);
  const totalPaise = taxPaise === null ? null : subtotalPaise + taxPaise;

  // Completion progress for live animated paper progress bar
  const completedChecks = [
    Boolean(values.customer_id),
    Boolean(values.invoice_date && values.due_date),
    Boolean(values.description.trim()),
    lines.some((l) => l.description.trim() && lineTotalPaise(l) !== null),
  ];
  const completionPct = Math.round(
    (completedChecks.filter(Boolean).length / completedChecks.length) * 100
  );

  function buildValidationValues() {
    return {
      ...values,
      items: lines.map((line) => ({
        description: line.description,
        quantity: line.quantity,
        unit_price: line.unit_price,
      })),
    };
  }

  function buildPayload() {
    const description = values.description.trim();
    const notes = values.notes.trim();
    if (locked) {
      return { description, notes };
    }
    return {
      customer_id: Number(values.customer_id),
      invoice_number: values.invoice_number.trim(),
      invoice_date: values.invoice_date,
      due_date: values.due_date,
      description,
      notes,
      tax_percent: Number(values.tax_percent.trim()),
      items: lines.map((line) => ({
        product_id: line.product_id ? Number(line.product_id) : null,
        description: line.description.trim(),
        quantity: Number(line.quantity.trim()),
        unit_price: line.unit_price.trim(),
      })),
    };
  }

  function validateStepAndAdvance(nextStep) {
    if (nextStep < step) {
      setStep(nextStep);
      return;
    }
    const allErrors = validateInvoiceForm(buildValidationValues());
    if (step === 1 && !locked) {
      const step1Errors = pick(allErrors, [
        "customer_id",
        "invoice_date",
        "due_date",
        "description",
      ]);
      if (Object.keys(step1Errors).length > 0) {
        setErrors((cur) => ({ ...cur, ...step1Errors }));
        return;
      }
    }
    if (step === 2 && !locked) {
      const step2Errors = Object.fromEntries(
        Object.entries(allErrors).filter(
          ([k]) => k === "tax_percent" || k === "items" || LINE_FIELD_PATTERN.test(k)
        )
      );
      if (Object.keys(step2Errors).length > 0) {
        setErrors((cur) => ({ ...cur, ...step2Errors }));
        return;
      }
    }
    setStep(nextStep);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return;
    setFormError(null);

    const clientErrors = validateInvoiceForm(buildValidationValues());
    const nextErrors = locked ? pick(clientErrors, ["description"]) : clientErrors;
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      // Jump to the first step that contains an error
      if (
        nextErrors.customer_id ||
        nextErrors.invoice_date ||
        nextErrors.due_date ||
        nextErrors.description
      ) {
        setStep(1);
      } else {
        setStep(2);
      }
      return;
    }

    setSubmitting(true);
    try {
      const payload = buildPayload();
      if (isEdit) {
        await updateInvoice(id, payload);
        showToast("success", "Invoice updated.");
        navigate(`/invoices/${id}`);
      } else {
        const created = await createInvoice(payload);
        // Only trigger the 2D generated stamp animation AFTER backend 201 succeeds!
        setGeneratedInvoice(created);
        showToast("success", `Invoice ${created.invoice_number} saved as draft.`);
        setTimeout(() => {
          navigate(`/invoices/${created.id}`);
        }, 1050);
      }
    } catch (error) {
      const mapped = {};
      const unmapped = [];
      Object.entries(error?.fieldErrors ?? {}).forEach(([key, message]) => {
        if (isKnownErrorKey(key)) mapped[key] = message;
        else unmapped.push(message);
      });
      setErrors(mapped);
      setFormError(
        unmapped[0] || error?.message || "Could not save invoice. Please check the highlighted fields."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      {header}

      {locked && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200">
          This invoice has active payments recorded. Amounts, dates, customer, and line items are locked — only description and notes can be edited.
        </div>
      )}

      {formError && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200"
        >
          {formError}
        </div>
      )}

      {/* Stepper Bar */}
      <nav aria-label="Invoice creation steps" className={`${CARD} p-3`}>
        <ol className="grid grid-cols-3 gap-2">
          {STEPS.map((s) => {
            const active = step === s.id;
            const done = step > s.id;
            return (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => validateStepAndAdvance(s.id)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-all ${
                    active
                      ? "bg-brand-50 text-brand-700 ring-1 ring-brand-200 dark:bg-brand-500/15 dark:text-brand-300 dark:ring-brand-500/30"
                      : "text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800/70"
                  }`}
                >
                  <span
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                      done
                        ? "bg-emerald-600 text-white"
                        : active
                        ? "bg-brand-600 text-white"
                        : "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                    }`}
                  >
                    {done ? <Check className="h-3.5 w-3.5" /> : s.id}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-xs font-semibold">{s.title}</p>
                    <p className="hidden truncate text-[11px] opacity-75 sm:block">{s.subtitle}</p>
                  </div>
                </button>
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Two-column Studio Layout: Left Interactive Form, Right Live 2D Animated Document Sheet */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <form onSubmit={handleSubmit} className="space-y-5 xl:col-span-7">
          {/* STEP 1: Client & Schedule */}
          {step === 1 && (
            <div key="step-1" className={`${CARD} animate-fade-slide-up space-y-5 p-6`}>
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                  1. Client & Billing Schedule
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Choose the customer and set billing and due dates.
                </p>
              </div>

              <Select
                id="customer_id"
                label="Customer *"
                value={values.customer_id}
                disabled={locked}
                error={errors.customer_id}
                onChange={(e) => setField("customer_id", e.target.value)}
              >
                <option value="">Select a customer…</option>
                {customers.map((c) => (
                  <option key={c.id} value={String(c.id)}>
                    {c.name}
                  </option>
                ))}
              </Select>

              <Input
                id="description"
                label="Invoice Summary / Title *"
                placeholder="e.g. Monthly Operations Retainer — November"
                value={values.description}
                error={errors.description}
                onChange={(e) => setField("description", e.target.value)}
              />

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Input
                  id="invoice_date"
                  type="date"
                  label="Invoice Date *"
                  value={values.invoice_date}
                  disabled={locked}
                  error={errors.invoice_date}
                  onChange={(e) => setField("invoice_date", e.target.value)}
                />
                <div className="space-y-1.5">
                  <Input
                    id="due_date"
                    type="date"
                    label="Due Date *"
                    value={values.due_date}
                    disabled={locked}
                    error={errors.due_date}
                    onChange={(e) => setField("due_date", e.target.value)}
                  />
                  {!locked && (
                    <div className="flex items-center gap-1.5">
                      {[7, 15, 30].map((d) => (
                        <button
                          key={d}
                          type="button"
                          onClick={() => setField("due_date", addDaysIso(values.invoice_date, d))}
                          className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 hover:bg-brand-50 hover:text-brand-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-brand-500/20 dark:hover:text-brand-300"
                        >
                          +{d}d
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <Input
                id="invoice_number"
                label="Invoice Number (optional)"
                placeholder="Leave blank to auto-generate (e.g. INV-0011)"
                value={values.invoice_number}
                disabled={locked}
                error={errors.invoice_number}
                onChange={(e) => setField("invoice_number", e.target.value)}
              />

              <div className="flex justify-end border-t border-slate-200 pt-4 dark:border-slate-800">
                <Button onClick={() => validateStepAndAdvance(2)}>
                  Next: Line Items & GST
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* STEP 2: Line Items & GST */}
          {step === 2 && (
            <div key="step-2" className={`${CARD} animate-fade-slide-up space-y-5 p-6`}>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                    2. Line Items & GST
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Exact integer-paise math with round-half-up GST calculation.
                  </p>
                </div>
                {!locked && (
                  <Button variant="secondary" onClick={addLine}>
                    <Plus className="h-4 w-4" />
                    Add item
                  </Button>
                )}
              </div>

              {errors.items && (
                <p className="text-xs font-medium text-red-600 dark:text-red-400">{errors.items}</p>
              )}

              <div className="space-y-3">
                {lines.map((line, index) => {
                  const rowTotal = lineTotals[index];
                  return (
                    <div
                      key={line.key}
                      className="animate-fade-slide-up rounded-xl border border-slate-200 bg-slate-50/70 p-4 dark:border-slate-700/80 dark:bg-slate-900/50"
                    >
                      <div className="mb-3 flex items-center justify-between">
                        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                          Item #{index + 1}
                        </span>
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-semibold tabular-nums text-brand-700 dark:text-brand-300">
                            {rowTotal !== null ? formatPaiseToRupees(rowTotal) : "—"}
                          </span>
                          {!locked && lines.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeLine(index)}
                              aria-label={`Remove item ${index + 1}`}
                              className="rounded-lg p-1 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-500/15 dark:hover:text-red-400"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </div>

                      {!locked && catalogue.length > 0 && (
                        <div className="mb-3">
                          <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                            Pick from Catalogue (Optional)
                          </label>
                          <select
                            value={line.product_id ? String(line.product_id) : ""}
                            onChange={(e) => {
                              const chosenId = e.target.value;
                              if (!chosenId) {
                                setLines((cur) =>
                                  cur.map((l, i) => (i === index ? { ...l, product_id: null } : l))
                                );
                                return;
                              }
                              const prod = catalogue.find((p) => String(p.id) === chosenId);
                              if (!prod) return;
                              setLines((cur) =>
                                cur.map((l, i) =>
                                  i === index
                                    ? {
                                        ...l,
                                        product_id: prod.id,
                                        description: prod.name,
                                        unit_price: paiseToRupeeInput(prod.selling_price_paise),
                                      }
                                    : l
                                )
                              );
                              setErrors((cur) => withoutItemErrors(cur));
                            }}
                            className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs text-slate-800 dark:text-slate-100"
                          >
                            <option value="">Custom line item…</option>
                            {catalogue.map((p) => (
                              <option key={p.id} value={String(p.id)}>
                                {p.name} — {formatPaiseToRupees(p.selling_price_paise)}
                                {p.item_type === "product"
                                  ? ` (Stock: ${p.stock_quantity} ${p.unit})`
                                  : " (Service)"}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-12">
                        <div className="sm:col-span-6">
                          <Input
                            id={`item-desc-${index}`}
                            label="Description *"
                            placeholder="Service or product description"
                            value={line.description}
                            disabled={locked}
                            error={errors[`items.${index}.description`]}
                            onChange={(e) => setLineField(index, "description", e.target.value)}
                          />
                        </div>
                        <div className="sm:col-span-2">
                          <Input
                            id={`item-qty-${index}`}
                            label="Qty *"
                            inputMode="numeric"
                            value={line.quantity}
                            disabled={locked}
                            error={errors[`items.${index}.quantity`]}
                            onChange={(e) => setLineField(index, "quantity", e.target.value)}
                          />
                        </div>
                        <div className="sm:col-span-4">
                          <Input
                            id={`item-price-${index}`}
                            label="Unit Price (₹) *"
                            placeholder="10000.00"
                            inputMode="decimal"
                            value={line.unit_price}
                            disabled={locked}
                            error={errors[`items.${index}.unit_price`]}
                            onChange={(e) => setLineField(index, "unit_price", e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Tax Percent */}
              <div className="grid grid-cols-1 items-end gap-4 border-t border-slate-200 pt-4 dark:border-slate-800 sm:grid-cols-2">
                <Input
                  id="tax_percent"
                  label="GST / Tax (%)"
                  inputMode="numeric"
                  value={values.tax_percent}
                  disabled={locked}
                  error={errors.tax_percent}
                  onChange={(e) => setField("tax_percent", e.target.value)}
                />
                {!locked && (
                  <div className="flex flex-wrap items-center gap-1.5 pb-1">
                    {[0, 5, 12, 18, 28].map((pct) => (
                      <button
                        key={pct}
                        type="button"
                        onClick={() => setField("tax_percent", String(pct))}
                        className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                          values.tax_percent === String(pct)
                            ? "bg-brand-600 text-white"
                            : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                        }`}
                      >
                        {pct}%
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
                <Button variant="secondary" onClick={() => setStep(1)}>
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button onClick={() => validateStepAndAdvance(3)}>
                  Next: Review & Issue
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* STEP 3: Notes & Generate */}
          {step === 3 && (
            <div key="step-3" className={`${CARD} animate-fade-slide-up space-y-5 p-6`}>
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                  3. Notes & Final Generation
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Add optional payment instructions or remarks, then generate your invoice.
                </p>
              </div>

              <Textarea
                id="notes"
                label="Payment Notes / Terms (optional)"
                rows={4}
                placeholder="Thank you for your business. Please include invoice number in your UPI/NEFT reference."
                value={values.notes}
                error={errors.notes}
                onChange={(e) => setField("notes", e.target.value)}
              />

              <div className="rounded-xl border border-brand-200 bg-brand-50/50 p-4 text-xs text-brand-900 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-200">
                <p className="font-semibold">Ready to create draft</p>
                <p className="mt-1 opacity-90">
                  New invoices are created in <strong>Draft</strong> status so you can review or print before marking them as <strong>Sent</strong>.
                </p>
              </div>

              <div className="flex items-center justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
                <Button variant="secondary" onClick={() => setStep(2)}>
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button type="submit" loading={submitting} disabled={Boolean(generatedInvoice)}>
                  <FileCheck2 className="h-4 w-4" />
                  {isEdit ? "Save Changes" : "Generate Draft Invoice"}
                </Button>
              </div>
            </div>
          )}
        </form>

        {/* RIGHT COLUMN: Live 2D Animated Document Preview Sheet */}
        <div className="xl:col-span-5">
          <div className="sticky top-24 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="inline-flex items-center gap-1.5 font-semibold text-slate-600 dark:text-slate-300">
                <Sparkles className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
                Live 2D Document Preview
              </span>
              <span className="font-medium tabular-nums text-slate-500 dark:text-slate-400">
                {completionPct}% complete
              </span>
            </div>

            {/* Animated 2D Paper Sheet — intentionally crisp white document surface */}
            <div
              className={`invoice-paper relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 text-slate-900 shadow-lg transition-all duration-300 ${
                generatedInvoice ? "ring-2 ring-emerald-500" : "animate-sheet-pulse"
              }`}
            >
              {/* Top Completion Progress Ribbon */}
              <div className="absolute inset-x-0 top-0 h-1.5 bg-slate-100">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 to-emerald-500 transition-all duration-300"
                  style={{ width: `${generatedInvoice ? 100 : completionPct}%` }}
                />
              </div>

              {/* 2D Animated Stamp ONLY when backend creation genuinely succeeds */}
              {generatedInvoice && (
                <div className="pointer-events-none absolute right-5 top-8 z-10 animate-stamp-in rounded-xl border-2 border-emerald-600 bg-emerald-50/95 px-3 py-1.5 text-center shadow-md">
                  <div className="flex items-center gap-1 text-xs font-extrabold uppercase tracking-widest text-emerald-700">
                    <CheckCircle2 className="h-4 w-4" />
                    Draft Created
                  </div>
                  <div className="text-[10px] font-semibold text-emerald-600">
                    {generatedInvoice.invoice_number}
                  </div>
                </div>
              )}

              {/* Sheet Header */}
              <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-4 pt-1 invoice-paper-border">
                <div className="flex items-center gap-3">
                  {businessSettings?.logo_url && (
                    <img
                      src={businessSettings.logo_url}
                      alt={businessSettings.business_name || "Business Logo"}
                      className="h-10 w-10 rounded-lg object-cover border border-slate-200 bg-white shrink-0"
                    />
                  )}
                  <div>
                    <p className="text-sm font-bold text-slate-900 invoice-paper-ink">
                      {businessSettings?.business_name || "Your Business"}
                    </p>
                    <p className="mt-0.5 text-[11px] text-slate-500 invoice-paper-ink">
                      {businessSettings?.gstin ? `GSTIN: ${businessSettings.gstin}` : "Tax Invoice"}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold uppercase tracking-widest text-brand-700">
                    INVOICE
                  </p>
                  <p className="mt-0.5 font-mono text-xs text-slate-600 invoice-paper-ink">
                    {generatedInvoice?.invoice_number || values.invoice_number.trim() || "AUTO-GEN"}
                  </p>
                </div>
              </div>

              {/* Bill To & Dates */}
              <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
                <div className="rounded-lg bg-slate-50 p-2.5 invoice-paper-subtle">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Billed To
                  </p>
                  <p className="mt-1 font-semibold text-slate-900 invoice-paper-ink">
                    {selectedCustomer?.name || "Select a customer…"}
                  </p>
                  {values.description.trim() && (
                    <p className="mt-0.5 line-clamp-2 text-[11px] text-slate-600 invoice-paper-ink">
                      {values.description.trim()}
                    </p>
                  )}
                </div>
                <div className="space-y-1.5 text-right">
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                      Issue Date
                    </span>
                    <p className="font-medium text-slate-800 invoice-paper-ink">
                      {values.invoice_date ? formatDate(values.invoice_date) : "—"}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                      Due Date
                    </span>
                    <p className="font-medium text-slate-800 invoice-paper-ink">
                      {values.due_date ? formatDate(values.due_date) : "—"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Animated Line Items Table */}
              <div className="mt-5">
                <div className="grid grid-cols-12 border-b border-slate-200 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400 invoice-paper-border">
                  <span className="col-span-6">Item</span>
                  <span className="col-span-2 text-right">Qty</span>
                  <span className="col-span-4 text-right">Amount</span>
                </div>
                <div className="divide-y divide-slate-100">
                  {lines.map((line, idx) => {
                    const rowPaise = lineTotals[idx];
                    return (
                      <div
                        key={line.key}
                        className="animate-fade-slide-up grid grid-cols-12 items-center py-2 text-xs"
                      >
                        <span className="col-span-6 truncate pr-2 font-medium text-slate-800 invoice-paper-ink">
                          {line.description.trim() || `Line item ${idx + 1}`}
                        </span>
                        <span className="col-span-2 text-right tabular-nums text-slate-600 invoice-paper-ink">
                          {line.quantity || "—"}
                        </span>
                        <span className="col-span-4 text-right font-semibold tabular-nums text-slate-900 invoice-paper-ink">
                          {rowPaise !== null ? formatPaiseToRupees(rowPaise) : "₹0.00"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Totals Box */}
              <div className="mt-4 space-y-1.5 border-t border-slate-200 pt-3 text-xs invoice-paper-border">
                <div className="flex justify-between text-slate-600 invoice-paper-ink">
                  <span>Subtotal</span>
                  <span className="tabular-nums">{formatPaiseToRupees(subtotalPaise)}</span>
                </div>
                <div className="flex justify-between text-slate-600 invoice-paper-ink">
                  <span>GST ({taxPercent ?? 0}%)</span>
                  <span className="tabular-nums">
                    {taxPaise !== null ? formatPaiseToRupees(taxPaise) : "—"}
                  </span>
                </div>
                <div className="flex justify-between border-t border-slate-200 pt-2 text-sm font-bold text-slate-900 invoice-paper-border invoice-paper-ink">
                  <span>Total Payable</span>
                  <span className="tabular-nums text-brand-700">
                    {totalPaise !== null ? formatPaiseToRupees(totalPaise) : "—"}
                  </span>
                </div>
              </div>

              {values.notes.trim() && (
                <div className="mt-4 rounded-lg bg-slate-50 p-2.5 text-[11px] text-slate-600 invoice-paper-subtle invoice-paper-ink">
                  <span className="font-semibold">Notes: </span>
                  {values.notes.trim()}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

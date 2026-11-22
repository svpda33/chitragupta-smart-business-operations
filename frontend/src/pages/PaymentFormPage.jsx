import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, Wallet } from "lucide-react";
import Button from "../components/common/Button.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import Input from "../components/common/Input.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import Select from "../components/common/Select.jsx";
import Textarea from "../components/common/Textarea.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "../context/ToastContext.jsx";
import { listInvoices } from "../services/invoiceService.js";
import { createPayment } from "../services/paymentService.js";
import { isBeforeIso, todayIso } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";
import { paiseToRupeeInput, validateRupeeInput } from "../utils/money.js";

const CARD = "rounded-xl border border-slate-200 bg-white p-6 shadow-sm";
const METHOD_OPTIONS = [
  { value: "upi", label: "UPI (Google Pay, PhonePe, Paytm)" },
  { value: "bank_transfer", label: "Bank Transfer (NEFT / IMPS / RTGS)" },
  { value: "cash", label: "Cash" },
  { value: "other", label: "Other / Cheque" },
];

export default function PaymentFormPage() {
  const [searchParams] = useSearchParams();
  const initialInvoiceId = searchParams.get("invoiceId") || "";
  const navigate = useNavigate();
  const showToast = useToast();

  const [selectedInvoiceId, setSelectedInvoiceId] = useState(initialInvoiceId);
  const [amount, setAmount] = useState("");
  const [paymentDate, setPaymentDate] = useState(todayIso());
  const [method, setMethod] = useState("upi");
  const [reference, setReference] = useState("");
  const [notes, setNotes] = useState("");

  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Fetch sent invoices with outstanding balances
  const { data: invoicesData, loading, error, refresh } = useAsync(
    () => listInvoices({ page_size: 100 }),
    []
  );

  const eligibleInvoices = (invoicesData?.items ?? []).filter(
    (inv) => inv.lifecycle === "sent" && inv.outstanding_paise > 0
  );

  const selectedInvoice = eligibleInvoices.find(
    (inv) => String(inv.id) === String(selectedInvoiceId)
  );

  useEffect(() => {
    if (selectedInvoice && !amount) {
      setAmount(paiseToRupeeInput(selectedInvoice.outstanding_paise));
    }
  }, [selectedInvoice, amount]);

  const handleInvoiceChange = (e) => {
    const newId = e.target.value;
    setSelectedInvoiceId(newId);
    const matched = eligibleInvoices.find((inv) => String(inv.id) === String(newId));
    if (matched) {
      setAmount(paiseToRupeeInput(matched.outstanding_paise));
    } else {
      setAmount("");
    }
  };

  const handleQuickFill = (percent) => {
    if (!selectedInvoice) return;
    const paise = Math.round((selectedInvoice.outstanding_paise * percent) / 100);
    setAmount(paiseToRupeeInput(paise));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;

    const errors = {};
    if (!selectedInvoiceId) {
      errors.invoice_id = "Please select an invoice.";
    }
    const amtError = validateRupeeInput(amount);
    if (amtError) {
      errors.amount = amtError;
    }
    if (!paymentDate) {
      errors.payment_date = "Payment date is required.";
    } else if (isBeforeIso(todayIso(), paymentDate)) {
      errors.payment_date = "Payment date cannot be in the future.";
    }
    if (!method) {
      errors.method = "Choose a payment method.";
    }

    setFieldErrors(errors);
    setFormError("");
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);
    try {
      await createPayment({
        invoice_id: Number(selectedInvoiceId),
        amount: amount.trim(),
        payment_date: paymentDate,
        method,
        reference: reference.trim() || null,
        notes: notes.trim() || null,
      });
      showToast("success", `Payment of ₹${amount} recorded successfully.`);
      navigate(`/invoices/${selectedInvoiceId}`);
    } catch (err) {
      setFormError(err.message || "Failed to record payment.");
      setFieldErrors(err.fieldErrors || {});
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingState label="Loading eligible invoices…" />;
  if (error) return <ErrorState message={error.message} onRetry={refresh} />;

  const invoiceOptions = [
    { value: "", label: "Select an unpaid invoice…" },
    ...eligibleInvoices.map((inv) => ({
      value: String(inv.id),
      label: `${inv.invoice_number} — ${inv.customer_name} (Due ${formatPaiseToRupees(inv.outstanding_paise)})`,
    })),
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-2">
        <Link
          to="/payments"
          className="inline-flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Payments
        </Link>
      </div>

      <PageHeader
        title="Record Received Payment"
        description="Record incoming cash, bank transfer or UPI payments against issued invoices."
      />

      {formError && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 border border-red-200">
          {formError}
        </div>
      )}

      {eligibleInvoices.length === 0 ? (
        <div className={`${CARD} text-center`}>
          <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500" />
          <h3 className="mt-3 text-base font-semibold text-slate-900">All Invoices Paid!</h3>
          <p className="mt-1 text-sm text-slate-600">
            There are currently no sent invoices with outstanding balances.
          </p>
          <div className="mt-5">
            <Link
              to="/invoices/new"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              Create new invoice
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className={`${CARD} space-y-5`}>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Select Invoice <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedInvoiceId}
              onChange={handleInvoiceChange}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              {invoiceOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            {fieldErrors.invoice_id && (
              <p className="mt-1 text-xs text-red-600">{fieldErrors.invoice_id}</p>
            )}
          </div>

          {selectedInvoice && (
            <div className="rounded-lg bg-slate-50 p-4 border border-slate-200 text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-600">Customer:</span>
                <span className="font-semibold text-slate-900">{selectedInvoice.customer_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Total Invoiced:</span>
                <span className="text-slate-900">{formatPaiseToRupees(selectedInvoice.total_paise)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Already Paid:</span>
                <span className="text-slate-900">{formatPaiseToRupees(selectedInvoice.paid_paise)}</span>
              </div>
              <div className="flex justify-between border-t border-slate-200 pt-2 font-medium">
                <span className="text-slate-900">Outstanding Balance:</span>
                <span className="text-brand-600 font-bold">
                  {formatPaiseToRupees(selectedInvoice.outstanding_paise)}
                </span>
              </div>
            </div>
          )}

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-sm font-medium text-slate-700">
                Payment Amount (₹) <span className="text-red-500">*</span>
              </label>
              {selectedInvoice && (
                <div className="flex gap-1.5 text-xs">
                  <button
                    type="button"
                    onClick={() => handleQuickFill(100)}
                    className="px-2 py-0.5 rounded bg-brand-50 text-brand-700 font-medium hover:bg-brand-100"
                  >
                    Full Balance
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickFill(50)}
                    className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium hover:bg-slate-200"
                  >
                    50%
                  </button>
                </div>
              )}
            </div>
            <Input
              type="text"
              placeholder="e.g. 25000.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              error={fieldErrors.amount}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Payment Date <span className="text-red-500">*</span>
              </label>
              <Input
                type="date"
                max={todayIso()}
                value={paymentDate}
                onChange={(e) => setPaymentDate(e.target.value)}
                error={fieldErrors.payment_date}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Payment Method <span className="text-red-500">*</span>
              </label>
              <Select
                options={METHOD_OPTIONS}
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                error={fieldErrors.method}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Transaction Reference / UTR
            </label>
            <Input
              type="text"
              placeholder="e.g. UPI/2026/02/9812948 or Cheque #401928"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              error={fieldErrors.reference}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
            <Textarea
              rows={2}
              placeholder="Optional notes or memos regarding this payment"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              error={fieldErrors.notes}
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
            <Link
              to="/payments"
              className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </Link>
            <Button type="submit" loading={submitting}>
              <Wallet className="h-4 w-4" />
              Record Payment
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}

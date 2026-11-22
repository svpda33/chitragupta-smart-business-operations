import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Pencil, Printer, Send, Trash2, Wallet } from "lucide-react";
import PageHeader from "../components/common/PageHeader.jsx";
import SummaryItem from "../components/common/SummaryItem.jsx";
import Button from "../components/common/Button.jsx";
import Input from "../components/common/Input.jsx";
import Select from "../components/common/Select.jsx";
import Textarea from "../components/common/Textarea.jsx";
import Modal from "../components/common/Modal.jsx";
import ConfirmDialog from "../components/common/ConfirmDialog.jsx";
import StatusBadge from "../components/common/StatusBadge.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { getInvoice, sendInvoice, deleteInvoice } from "../services/invoiceService.js";
import { updatePayment, reversePayment } from "../services/paymentService.js";
import { formatDate, isBeforeIso, todayIso } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";
import { paiseToRupeeInput, validateRupeeInput } from "../utils/money.js";

const CARD = "rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111827] shadow-sm";
const PRIMARY_LINK =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";
const SECONDARY_LINK =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";

const METHOD_LABELS = {
  cash: "Cash",
  bank_transfer: "Bank transfer",
  upi: "UPI",
  other: "Other",
};
const METHOD_OPTIONS = Object.entries(METHOD_LABELS).map(([value, label]) => ({ value, label }));
const LIFECYCLE_LABELS = { draft: "Draft", sent: "Sent" };
const REASON_MIN_LENGTH = 3;
const EMPTY_EDIT_FORM = { amount: "", payment_date: "", method: "", reference: "", notes: "" };

function messageOf(error, fallback = "Something went wrong. Please try again.") {
  return error?.message || fallback;
}

function formatDateTime(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function validateEditForm(form) {
  const errors = {};
  const amountError = validateRupeeInput(form.amount);
  if (amountError) {
    errors.amount = amountError;
  }
  if (!form.payment_date) {
    errors.payment_date = "Payment date is required.";
  } else if (isBeforeIso(todayIso(), form.payment_date)) {
    errors.payment_date = "Payment date cannot be in the future.";
  }
  if (!form.method) {
    errors.method = "Choose a payment method.";
  }
  return errors;
}

export default function InvoiceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { business } = useAuth();
  const showToast = useToast();
  const invoiceState = useAsync(() => getInvoice(id), [id]);
  const invoice = invoiceState.data;

  const [sending, setSending] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const [editPayment, setEditPayment] = useState(null);
  const [editForm, setEditForm] = useState(EMPTY_EDIT_FORM);
  const [editErrors, setEditErrors] = useState({});
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState(null);

  const [reversalTarget, setReversalTarget] = useState(null);
  const [reverseReason, setReverseReason] = useState("");
  const [reverseErrors, setReverseErrors] = useState({});
  const [reverseSaving, setReverseSaving] = useState(false);
  const [reverseError, setReverseError] = useState(null);

  if (invoiceState.error) {
    if (invoiceState.error.status === 404) {
      return (
        <div className={`${CARD} space-y-4 p-6 text-center`}>
          <p className="text-sm text-slate-700">This invoice could not be found.</p>
          <Link to="/invoices" className={SECONDARY_LINK}>
            Back to invoices
          </Link>
        </div>
      );
    }
    return (
      <ErrorState
        message={messageOf(invoiceState.error, "The invoice could not be loaded.")}
        onRetry={invoiceState.refresh}
      />
    );
  }

  if (!invoice) {
    return <LoadingState label="Loading invoice…" />;
  }

  const payments = invoice.payments ?? [];
  const history = [...(invoice.history ?? [])].sort(
    (a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)
  );
  const isDraft = invoice.lifecycle === "draft";
  const isSent = invoice.lifecycle === "sent";
  const locked = payments.some((payment) => payment.status === "active");
  const overdue = invoice.status === "overdue";
  const canRecordPayment = isSent && invoice.outstanding_paise > 0;

  async function handleSend() {
    setSending(true);
    try {
      await sendInvoice(id);
      invoiceState.refresh();
      showToast("success", "Invoice marked as sent.");
    } catch (error) {
      showToast("error", messageOf(error));
    } finally {
      setSending(false);
    }
  }

  function openDelete() {
    setDeleteError(null);
    setDeleteOpen(true);
  }

  function closeDelete() {
    setDeleteOpen(false);
    setDeleteError(null);
  }

  async function handleDelete() {
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteInvoice(id);
      navigate("/invoices");
      showToast("success", "Draft deleted.");
    } catch (error) {
      setDeleteError(messageOf(error));
      setDeleting(false);
    }
  }

  function openEditPayment(payment) {
    setEditPayment(payment);
    setEditForm({
      amount: paiseToRupeeInput(payment.amount_paise),
      payment_date: payment.payment_date ?? "",
      method: payment.method ?? "",
      reference: payment.reference ?? "",
      notes: payment.notes ?? "",
    });
    setEditErrors({});
    setEditError(null);
  }

  function closeEditPayment() {
    if (editSaving) return;
    setEditPayment(null);
  }

  function updateEditField(name, value) {
    setEditForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSaveEdit(event) {
    event.preventDefault();
    if (editSaving || !editPayment) return;

    const errors = validateEditForm(editForm);
    setEditErrors(errors);
    setEditError(null);
    if (Object.keys(errors).length > 0) return;

    setEditSaving(true);
    try {
      await updatePayment(editPayment.id, {
        amount: editForm.amount.trim(),
        payment_date: editForm.payment_date,
        method: editForm.method,
        reference: editForm.reference.trim(),
        notes: editForm.notes.trim(),
      });
      setEditPayment(null);
      invoiceState.refresh();
      showToast("success", "Payment updated.");
    } catch (error) {
      setEditError(messageOf(error));
      setEditErrors(error?.fieldErrors ?? {});
    } finally {
      setEditSaving(false);
    }
  }

  function openReversal(payment) {
    setReversalTarget(payment);
    setReverseReason("");
    setReverseErrors({});
    setReverseError(null);
  }

  function closeReversal() {
    if (reverseSaving) return;
    setReversalTarget(null);
  }

  async function handleReverse() {
    if (reverseSaving || !reversalTarget) return;

    const reason = reverseReason.trim();
    if (reason.length < REASON_MIN_LENGTH) {
      setReverseErrors({ reason: "Enter a reason of at least 3 characters." });
      setReverseError(null);
      return;
    }

    setReverseErrors({});
    setReverseError(null);
    setReverseSaving(true);
    try {
      await reversePayment(reversalTarget.id, reason);
      setReversalTarget(null);
      invoiceState.refresh();
      showToast("success", "Payment reversed.");
    } catch (error) {
      setReverseError(messageOf(error));
      setReverseErrors(error?.fieldErrors ?? {});
    } finally {
      setReverseSaving(false);
    }
  }

  const summaryItems = [
    { label: "Total", value: formatPaiseToRupees(invoice.total_paise) },
    { label: "Paid", value: formatPaiseToRupees(invoice.paid_paise) },
    {
      label: "Outstanding",
      value: formatPaiseToRupees(invoice.outstanding_paise),
      tone: overdue && invoice.outstanding_paise > 0 ? "danger" : undefined,
    },
    { label: "Due date", value: formatDate(invoice.due_date) },
  ];
  if (overdue) {
    summaryItems.push({ label: "Days overdue", value: `${invoice.days_overdue} days` });
  }

  const title = (
    <span className="flex flex-wrap items-center gap-3">
      {business?.logo_url && (
        <img
          src={business.logo_url}
          alt={business.name || "Business Logo"}
          className="h-9 w-9 rounded-lg object-cover border border-slate-200 dark:border-slate-700 bg-white"
        />
      )}
      <span>{invoice.invoice_number || "Invoice"}</span>
      <StatusBadge kind="invoice" value={invoice.status} />
      <span className="text-sm font-normal text-slate-600 dark:text-slate-400">
        {LIFECYCLE_LABELS[invoice.lifecycle] ?? invoice.lifecycle}
      </span>
    </span>
  );

  const actions = (
    <div className="no-print flex flex-wrap items-center gap-2">
      <Button variant="secondary" onClick={() => window.print()}>
        <Printer className="h-4 w-4" aria-hidden="true" />
        Print / PDF
      </Button>
      {locked ? (
        <>
          <Button variant="secondary" disabled>
            <Pencil className="h-4 w-4" aria-hidden="true" />
            Edit
          </Button>
          <span className="text-sm text-slate-600">Locked because payments are recorded.</span>
        </>
      ) : (
        <Link to={`/invoices/${id}/edit`} className={SECONDARY_LINK}>
          <Pencil className="h-4 w-4" aria-hidden="true" />
          Edit
        </Link>
      )}
      {isDraft ? (
        <Button variant="secondary" onClick={handleSend} loading={sending}>
          <Send className="h-4 w-4" aria-hidden="true" />
          Mark as sent
        </Button>
      ) : null}
      {isDraft ? (
        <Button variant="danger" onClick={openDelete}>
          <Trash2 className="h-4 w-4" aria-hidden="true" />
          Delete draft
        </Button>
      ) : null}
      {canRecordPayment ? (
        <Link to={`/payments/new?invoiceId=${id}`} className={PRIMARY_LINK}>
          <Wallet className="h-4 w-4" aria-hidden="true" />
          Record payment
        </Link>
      ) : null}
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader title={title} actions={actions} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {summaryItems.map((item) => (
          <SummaryItem key={item.label} label={item.label} value={item.value} tone={item.tone} />
        ))}
      </div>

      <section aria-labelledby="details-heading" className={`${CARD} p-5`}>
        <h2 id="details-heading" className="text-base font-semibold text-slate-900">
          Details
        </h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-slate-500">Customer</dt>
            <dd className="mt-1 text-sm">
              <Link to={`/customers/${invoice.customer_id}`} className="text-brand-700 hover:underline">
                {invoice.customer_name}
              </Link>
            </dd>
          </div>
          <div>
            <dt className="text-sm text-slate-500">Invoice date</dt>
            <dd className="mt-1 text-sm text-slate-900">{formatDate(invoice.invoice_date)}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-500">Sent on</dt>
            <dd className="mt-1 text-sm text-slate-900">
              {invoice.sent_at ? formatDateTime(invoice.sent_at) : "Not sent yet"}
            </dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-sm text-slate-500">Notes</dt>
            <dd className="mt-1 whitespace-pre-line text-sm text-slate-900">{invoice.notes || "—"}</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="items-heading" className={`${CARD} p-5`}>
        <h2 id="items-heading" className="text-base font-semibold text-slate-900">
          Line items
        </h2>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="text-left text-slate-600">
              <tr>
                <th scope="col" className="py-2 pr-4 font-medium">Description</th>
                <th scope="col" className="py-2 pr-4 text-right font-medium">Quantity</th>
                <th scope="col" className="py-2 pr-4 text-right font-medium">Unit price</th>
                <th scope="col" className="py-2 text-right font-medium">Line total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {invoice.items.map((item) => (
                <tr key={item.id}>
                  <td className="py-2 pr-4 text-slate-900">{item.description}</td>
                  <td className="py-2 pr-4 text-right tabular-nums">{item.quantity}</td>
                  <td className="py-2 pr-4 text-right tabular-nums">
                    {formatPaiseToRupees(item.unit_price_paise)}
                  </td>
                  <td className="py-2 text-right tabular-nums">{formatPaiseToRupees(item.line_total_paise)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <dl className="ml-auto mt-4 w-full max-w-xs space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-slate-600">Subtotal</dt>
            <dd className="tabular-nums text-slate-900">{formatPaiseToRupees(invoice.subtotal_paise)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Tax ({invoice.tax_percent}%)</dt>
            <dd className="tabular-nums text-slate-900">{formatPaiseToRupees(invoice.tax_paise)}</dd>
          </div>
          <div className="flex justify-between border-t border-slate-200 pt-2 font-semibold">
            <dt className="text-slate-900">Total</dt>
            <dd className="tabular-nums text-slate-900">{formatPaiseToRupees(invoice.total_paise)}</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="payments-heading" className={`${CARD} p-5`}>
        <h2 id="payments-heading" className="text-base font-semibold text-slate-900">
          Payments
        </h2>
        {payments.length === 0 ? (
          <p className="mt-4 text-sm text-slate-600">No payments recorded yet.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="text-left text-slate-600">
                <tr>
                  <th scope="col" className="py-2 pr-4 font-medium">Date</th>
                  <th scope="col" className="py-2 pr-4 text-right font-medium">Amount</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Method</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Reference</th>
                  <th scope="col" className="py-2 pr-4 font-medium">Status</th>
                  <th scope="col" className="py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {payments.map((payment) => (
                  <tr key={payment.id}>
                    <td className="py-2 pr-4 text-slate-900">{formatDate(payment.payment_date)}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">
                      {formatPaiseToRupees(payment.amount_paise)}
                    </td>
                    <td className="py-2 pr-4 text-slate-700">{METHOD_LABELS[payment.method] ?? payment.method}</td>
                    <td className="py-2 pr-4 text-slate-700">{payment.reference || "—"}</td>
                    <td className="py-2 pr-4">
                      <StatusBadge kind="payment" value={payment.status} />
                      {payment.status === "reversed" && payment.reversal_reason ? (
                        <p className="mt-1 text-xs text-slate-500">Reason: {payment.reversal_reason}</p>
                      ) : null}
                    </td>
                    <td className="py-2">
                      {payment.status === "active" ? (
                        <div className="flex flex-wrap gap-2">
                          <Button variant="secondary" className="px-3 py-1.5" onClick={() => openEditPayment(payment)}>
                            Edit
                          </Button>
                          <Button variant="secondary" className="px-3 py-1.5" onClick={() => openReversal(payment)}>
                            Reverse
                          </Button>
                        </div>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section aria-labelledby="history-heading" className={`${CARD} p-5`}>
        <h2 id="history-heading" className="text-base font-semibold text-slate-900">
          History
        </h2>
        {history.length === 0 ? (
          <p className="mt-4 text-sm text-slate-600">No activity yet.</p>
        ) : (
          <ol className="mt-4 space-y-3">
            {history.map((entry) => (
              <li key={entry.id} className="border-l-2 border-slate-200 pl-3">
                <p className="text-sm text-slate-900">{entry.summary}</p>
                <p className="text-xs text-slate-500">{formatDateTime(entry.created_at)}</p>
              </li>
            ))}
          </ol>
        )}
      </section>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete draft invoice?"
        message="This draft will be removed. This cannot be undone."
        confirmLabel="Delete draft"
        variant="danger"
        loading={deleting}
        errorMessage={deleteError}
        onConfirm={handleDelete}
        onCancel={closeDelete}
      />

      <Modal
        open={Boolean(editPayment)}
        title="Edit payment"
        onClose={closeEditPayment}
        footer={
          <>
            <Button variant="secondary" onClick={closeEditPayment} disabled={editSaving}>
              Cancel
            </Button>
            <Button type="submit" form="edit-payment-form" loading={editSaving}>
              Save payment
            </Button>
          </>
        }
      >
        <form id="edit-payment-form" noValidate onSubmit={handleSaveEdit} className="space-y-4">
          {editError ? (
            <p role="alert" className="text-sm text-red-700">
              {editError}
            </p>
          ) : null}
          <Input
            id="edit-payment-amount"
            name="amount"
            label="Amount (₹)"
            inputMode="decimal"
            value={editForm.amount}
            onChange={(event) => updateEditField("amount", event.target.value)}
            error={editErrors.amount}
          />
          <Input
            id="edit-payment-date"
            type="date"
            name="payment_date"
            label="Payment date"
            max={todayIso()}
            value={editForm.payment_date}
            onChange={(event) => updateEditField("payment_date", event.target.value)}
            error={editErrors.payment_date}
          />
          <Select
            id="edit-payment-method"
            name="method"
            label="Method"
            value={editForm.method}
            onChange={(event) => updateEditField("method", event.target.value)}
            error={editErrors.method}
          >
            <option value="">Choose a method</option>
            {METHOD_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Input
            id="edit-payment-reference"
            name="reference"
            label="Reference"
            value={editForm.reference}
            onChange={(event) => updateEditField("reference", event.target.value)}
            error={editErrors.reference}
          />
          <Input
            id="edit-payment-notes"
            name="notes"
            label="Notes"
            value={editForm.notes}
            onChange={(event) => updateEditField("notes", event.target.value)}
            error={editErrors.notes}
          />
        </form>
      </Modal>

      <Modal
        open={Boolean(reversalTarget)}
        title="Reverse payment"
        onClose={closeReversal}
        footer={
          <>
            <Button variant="secondary" onClick={closeReversal} disabled={reverseSaving}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleReverse} loading={reverseSaving}>
              Reverse payment
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {reverseError ? (
            <p role="alert" className="text-sm text-red-700">
              {reverseError}
            </p>
          ) : null}
          <Textarea
            id="reverse-payment-reason"
            name="reason"
            label="Reason"
            rows={3}
            required
            value={reverseReason}
            onChange={(event) => setReverseReason(event.target.value)}
            error={reverseErrors.reason}
          />
        </div>
      </Modal>
    </div>
  );
}

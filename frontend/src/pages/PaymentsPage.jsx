import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, RotateCcw, Search, Wallet, XCircle } from "lucide-react";
import Button from "../components/common/Button.jsx";
import ConfirmDialog from "../components/common/ConfirmDialog.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import Modal from "../components/common/Modal.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import Pagination from "../components/common/Pagination.jsx";
import SearchInput from "../components/common/SearchInput.jsx";
import Select from "../components/common/Select.jsx";
import StatusBadge from "../components/common/StatusBadge.jsx";
import SummaryItem from "../components/common/SummaryItem.jsx";
import Textarea from "../components/common/Textarea.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useDebouncedValue } from "../hooks/useDebouncedValue.js";
import { useToast } from "../context/ToastContext.jsx";
import { listPayments, reversePayment } from "../services/paymentService.js";
import { listCustomers } from "../services/customerService.js";
import { formatDate } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";

const PAGE_SIZE = 20;
const CARD = "rounded-xl border border-slate-200 bg-white shadow-sm";
const PRIMARY_LINK =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";

const STATUS_OPTIONS = [
  { value: "", label: "All payments" },
  { value: "active", label: "Active" },
  { value: "reversed", label: "Reversed" },
];

const METHOD_LABELS = {
  cash: "Cash",
  bank_transfer: "Bank Transfer",
  upi: "UPI",
  other: "Other",
};

export default function PaymentsPage() {
  const [status, setStatus] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [page, setPage] = useState(1);
  const showToast = useToast();

  // Reversal modal state
  const [reversalTarget, setReversalTarget] = useState(null);
  const [reverseReason, setReverseReason] = useState("");
  const [reverseError, setReverseError] = useState("");
  const [reverseSaving, setReverseSaving] = useState(false);

  const customersState = useAsync(() => listCustomers({ page_size: 100 }), []);
  const customers = customersState.data?.items ?? [];

  const customerOptions = [
    { value: "", label: "All customers" },
    ...customers.map((c) => ({ value: String(c.id), label: c.name })),
  ];

  const paymentsState = useAsync(() => {
    const params = { page, page_size: PAGE_SIZE };
    if (status) params.status = status;
    if (customerId) params.customer_id = Number(customerId);
    return listPayments(params);
  }, [page, status, customerId]);

  const payments = paymentsState.data?.items ?? [];
  const total = paymentsState.data?.total ?? 0;

  // Aggregate stats from current items
  const activeTotalPaise = payments
    .filter((p) => p.status === "active")
    .reduce((acc, p) => acc + p.amount_paise, 0);
  const reversedCount = payments.filter((p) => p.status === "reversed").length;

  const handleOpenReverse = (pmt) => {
    setReversalTarget(pmt);
    setReverseReason("");
    setReverseError("");
  };

  const handleConfirmReverse = async () => {
    if (!reversalTarget || reverseSaving) return;
    const reason = reverseReason.trim();
    if (reason.length < 3) {
      setReverseError("Please provide a reason of at least 3 characters.");
      return;
    }

    setReverseSaving(true);
    setReverseError("");
    try {
      await reversePayment(reversalTarget.id, reason);
      showToast("success", `Payment #${reversalTarget.id} reversed.`);
      setReversalTarget(null);
      paymentsState.refresh();
    } catch (err) {
      setReverseError(err.message || "Failed to reverse payment.");
    } finally {
      setReverseSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payment History & Tracking"
        description="All recorded incoming payments, payment methods, transaction receipts and reversals."
        actions={
          <Link to="/payments/new" className={PRIMARY_LINK}>
            <Wallet className="h-4 w-4" />
            Record payment
          </Link>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <SummaryItem
          label="Active Payments Shown"
          value={formatPaiseToRupees(activeTotalPaise)}
          tone="success"
        />
        <SummaryItem
          label="Total Records"
          value={String(total)}
        />
        <SummaryItem
          label="Reversed Transactions"
          value={String(reversedCount)}
          tone={reversedCount > 0 ? "warning" : undefined}
        />
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="w-full sm:w-48">
          <Select
            options={STATUS_OPTIONS}
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="w-full sm:w-64">
          <Select
            options={customerOptions}
            value={customerId}
            onChange={(e) => {
              setCustomerId(e.target.value);
              setPage(1);
            }}
          />
        </div>
      </div>

      {paymentsState.loading && !paymentsState.data ? (
        <LoadingState label="Loading payments…" />
      ) : paymentsState.error ? (
        <ErrorState message={paymentsState.error.message} onRetry={paymentsState.refresh} />
      ) : payments.length === 0 ? (
        <EmptyState
          icon={Wallet}
          title="No payments found"
          message={
            status || customerId
              ? "No payments match the selected filters."
              : "No payments recorded yet. Record your first payment against a sent invoice."
          }
          action={
            <Link to="/payments/new" className={PRIMARY_LINK}>
              <Wallet className="h-4 w-4" />
              Record payment
            </Link>
          }
        />
      ) : (
        <div className="space-y-4">
          <div className={`${CARD} overflow-hidden`}>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                      Date
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                      Customer
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                      Invoice
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                      Method
                    </th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                      Reference / UTR
                    </th>
                    <th scope="col" className="px-4 py-3 text-right font-medium text-slate-600">
                      Amount
                    </th>
                    <th scope="col" className="px-4 py-3 text-center font-medium text-slate-600">
                      Status
                    </th>
                    <th scope="col" className="px-4 py-3 text-right font-medium text-slate-600">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {payments.map((p) => {
                    const isReversed = p.status === "reversed";
                    return (
                      <tr key={p.id} className={isReversed ? "bg-slate-50/70" : "hover:bg-slate-50/50"}>
                        <td className="whitespace-nowrap px-4 py-3.5 text-slate-600">
                          {formatDate(p.payment_date)}
                        </td>
                        <td className="px-4 py-3.5 font-medium text-slate-900">
                          <Link to={`/customers/${p.customer_id}`} className="hover:text-brand-600 hover:underline">
                            {p.customer_name}
                          </Link>
                        </td>
                        <td className="px-4 py-3.5 font-medium text-brand-600">
                          <Link to={`/invoices/${p.invoice_id}`} className="hover:underline">
                            {p.invoice_number}
                          </Link>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5 text-slate-600">
                          <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-800">
                            {METHOD_LABELS[p.method] || p.method}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-xs text-slate-500 font-mono">
                          {p.reference || "—"}
                        </td>
                        <td className={`whitespace-nowrap px-4 py-3.5 text-right font-semibold ${isReversed ? "line-through text-slate-400" : "text-emerald-700"}`}>
                          {formatPaiseToRupees(p.amount_paise)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5 text-center">
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              isReversed
                                ? "bg-red-50 text-red-700 border border-red-200"
                                : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            }`}
                          >
                            {isReversed ? "Reversed" : "Active"}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3.5 text-right">
                          {!isReversed ? (
                            <button
                              type="button"
                              onClick={() => handleOpenReverse(p)}
                              className="inline-flex items-center gap-1 text-xs font-medium text-red-600 hover:text-red-800 hover:underline"
                            >
                              <RotateCcw className="h-3.5 w-3.5" />
                              Reverse
                            </button>
                          ) : (
                            <span className="text-xs text-slate-400 italic" title={p.reversal_reason}>
                              Reason: {p.reversal_reason ? p.reversal_reason.slice(0, 20) + "…" : "—"}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={setPage}
          />
        </div>
      )}

      {/* Payment Reversal Modal */}
      {reversalTarget && (
        <Modal
          title={`Reverse Payment #${reversalTarget.id}`}
          open={Boolean(reversalTarget)}
          onClose={() => setReversalTarget(null)}
        >
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Reversing this payment of <strong className="text-slate-900">{formatPaiseToRupees(reversalTarget.amount_paise)}</strong> will mark it as reversed and restore the outstanding balance on invoice <strong className="text-slate-900">{reversalTarget.invoice_number}</strong>.
            </p>

            {reverseError && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200">
                {reverseError}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Reason for Reversal <span className="text-red-500">*</span>
              </label>
              <Textarea
                rows={3}
                placeholder="e.g. Cheque bounced, duplicate charge, client initiated chargeback"
                value={reverseReason}
                onChange={(e) => setReverseReason(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
              <Button variant="secondary" onClick={() => setReversalTarget(null)}>
                Cancel
              </Button>
              <Button variant="danger" loading={reverseSaving} onClick={handleConfirmReverse}>
                Confirm Reversal
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

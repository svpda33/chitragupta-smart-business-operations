import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { FileText, Pencil, Trash2 } from "lucide-react";
import Button from "../components/common/Button.jsx";
import ConfirmDialog from "../components/common/ConfirmDialog.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import StatusBadge from "../components/common/StatusBadge.jsx";
import SummaryItem from "../components/common/SummaryItem.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { deleteCustomer, getCustomer } from "../services/customerService.js";
import { listInvoices } from "../services/invoiceService.js";
import { useToast } from "../context/ToastContext.jsx";
import { formatPaiseToRupees } from "../utils/formatMoney.js";
import { formatDate } from "../utils/dates.js";

const SECONDARY_LINK_CLASSES =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";

const PRIMARY_LINK_CLASSES =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";

function orDash(value) {
  return typeof value === "string" && value.trim() !== "" ? value : "—";
}

function InfoField({ label, value, wide = false }) {
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className="mt-1 whitespace-pre-line break-words text-sm text-slate-900">{value}</dd>
    </div>
  );
}

export default function CustomerDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const showToast = useToast();

  const customerState = useAsync(() => getCustomer(id), [id]);
  const invoicesState = useAsync(
    () => listInvoices({ customer_id: id, page_size: 100 }),
    [id]
  );

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  const customer = customerState.data;

  if (customerState.error) {
    if (customerState.error.status === 404) {
      return (
        <div className="space-y-6">
          <PageHeader title="Customer not found" />
          <div className="rounded-xl border border-slate-200 bg-white p-6 text-center shadow-sm">
            <p className="text-sm text-slate-700">This customer could not be found.</p>
            <div className="mt-4">
              <Link to="/customers" className={SECONDARY_LINK_CLASSES}>
                Back to customers
              </Link>
            </div>
          </div>
        </div>
      );
    }
    return (
      <div className="space-y-6">
        <PageHeader title="Customer" />
        <ErrorState message={customerState.error.message} onRetry={customerState.refresh} />
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="space-y-6">
        <PageHeader title="Customer" />
        <LoadingState />
      </div>
    );
  }

  const handleCloseConfirm = () => {
    if (deleting) return;
    setConfirmOpen(false);
    setDeleteError("");
  };

  async function handleDelete() {
    if (deleting) return;
    setDeleting(true);
    setDeleteError("");
    try {
      await deleteCustomer(id);
      setConfirmOpen(false);
      showToast("success", "Customer deleted.");
      navigate("/customers");
    } catch (error) {
      setDeleteError(error?.message || "The customer could not be deleted. Please try again.");
      setDeleting(false);
    }
  }

  const invoices = invoicesState.data?.items ?? [];
  const overdueTone = customer.overdue_paise > 0 ? "danger" : undefined;
  const createdDate = customer.created_at ? String(customer.created_at).slice(0, 10) : "";

  let invoicesBody;
  if (invoicesState.error) {
    invoicesBody = (
      <ErrorState message={invoicesState.error.message} onRetry={invoicesState.refresh} />
    );
  } else if (invoicesState.loading && !invoicesState.data) {
    invoicesBody = <LoadingState />;
  } else if (invoices.length === 0) {
    invoicesBody = (
      <EmptyState
        icon={FileText}
        title="No invoices for this customer yet"
        action={
          <Link to={`/invoices/new?customerId=${id}`} className={PRIMARY_LINK_CLASSES}>
            <FileText className="h-4 w-4" aria-hidden="true" />
            Create invoice
          </Link>
        }
      />
    );
  } else {
    invoicesBody = (
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                Invoice
              </th>
              <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                Description
              </th>
              <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                Due date
              </th>
              <th scope="col" className="px-4 py-3 text-right font-medium text-slate-600">
                Total
              </th>
              <th scope="col" className="px-4 py-3 text-right font-medium text-slate-600">
                Outstanding
              </th>
              <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {invoices.map((invoice) => (
              <tr key={invoice.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Link
                    to={`/invoices/${invoice.id}`}
                    className="font-medium text-brand-700 hover:underline"
                  >
                    {invoice.invoice_number}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-700">{orDash(invoice.description)}</td>
                <td className="px-4 py-3 text-slate-700">{formatDate(invoice.due_date)}</td>
                <td className="px-4 py-3 text-right text-slate-700">
                  {formatPaiseToRupees(invoice.total_paise)}
                </td>
                <td className="px-4 py-3 text-right text-slate-700">
                  {formatPaiseToRupees(invoice.outstanding_paise)}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge kind="invoice" value={invoice.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={customer.name}
        actions={
          <>
            <Link to={`/customers/${id}/edit`} className={SECONDARY_LINK_CLASSES}>
              <Pencil className="h-4 w-4" aria-hidden="true" />
              Edit
            </Link>
            <Link to={`/invoices/new?customerId=${id}`} className={PRIMARY_LINK_CLASSES}>
              <FileText className="h-4 w-4" aria-hidden="true" />
              Create invoice
            </Link>
            <Button variant="secondary" onClick={() => setConfirmOpen(true)}>
              <Trash2 className="h-4 w-4" aria-hidden="true" />
              Delete
            </Button>
          </>
        }
      />

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-base font-semibold text-slate-900">Contact and business information</h2>
        <dl className="mt-4 grid gap-x-6 gap-y-5 sm:grid-cols-2">
          <InfoField label="Email" value={orDash(customer.email)} />
          <InfoField label="Phone" value={orDash(customer.phone)} />
          <InfoField label="Address" value={orDash(customer.address)} wide />
          <InfoField label="Notes" value={orDash(customer.notes)} wide />
          <InfoField label="Customer since" value={formatDate(createdDate)} />
        </dl>
      </section>

      <section aria-label="Outstanding summary">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <SummaryItem label="Outstanding" value={formatPaiseToRupees(customer.outstanding_paise)} />
          <SummaryItem label="Overdue" value={formatPaiseToRupees(customer.overdue_paise)} tone={overdueTone} />
          <SummaryItem label="Total invoiced" value={formatPaiseToRupees(customer.total_invoiced_paise)} />
          <SummaryItem label="Total paid" value={formatPaiseToRupees(customer.total_paid_paise)} />
          <SummaryItem label="Invoices" value={customer.invoice_count} />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold text-slate-900">Invoices</h2>
        {invoicesBody}
      </section>

      <ConfirmDialog
        open={confirmOpen}
        title="Delete customer?"
        message={`This permanently removes ${customer.name}. Customers with invoices cannot be deleted.`}
        confirmLabel="Delete customer"
        variant="danger"
        loading={deleting}
        errorMessage={deleteError}
        onConfirm={handleDelete}
        onCancel={handleCloseConfirm}
      />
    </div>
  );
}

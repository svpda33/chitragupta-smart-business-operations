import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { FilePlus, FileText } from "lucide-react";
import PageHeader from "../components/common/PageHeader.jsx";
import SearchInput from "../components/common/SearchInput.jsx";
import Select from "../components/common/Select.jsx";
import Button from "../components/common/Button.jsx";
import Pagination from "../components/common/Pagination.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import StatusBadge from "../components/common/StatusBadge.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useDebouncedValue } from "../hooks/useDebouncedValue.js";
import { listInvoices } from "../services/invoiceService.js";
import { listCustomers } from "../services/customerService.js";
import { formatDate } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";

const PAGE_SIZE = 20;
const CARD = "rounded-xl border border-slate-200 bg-white shadow-sm";
const PRIMARY_LINK =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "draft", label: "Draft" },
  { value: "pending", label: "Pending" },
  { value: "partially_paid", label: "Partly paid" },
  { value: "overdue", label: "Overdue" },
  { value: "paid", label: "Paid" },
];

function OverdueNote({ invoice }) {
  if (invoice.status !== "overdue" || typeof invoice.days_overdue !== "number") return null;
  return <span className="text-xs font-medium text-red-700">{invoice.days_overdue} days overdue</span>;
}

export default function InvoicesPage() {
  const [searchParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState(() => searchParams.get("status") || "");
  const [customerId, setCustomerId] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search, 300);

  const customersState = useAsync(() => listCustomers({ page_size: 100 }), []);
  const customers = customersState.data?.items ?? [];

  const invoicesState = useAsync(() => {
    const params = { page, page_size: PAGE_SIZE };
    const term = debouncedSearch.trim();
    if (term) params.search = term;
    if (status) params.status = status;
    if (customerId) params.customer_id = Number(customerId);
    return listInvoices(params);
  }, [page, debouncedSearch, status, customerId]);

  const filtersActive = search.trim() !== "" || status !== "" || customerId !== "";

  function clearFilters() {
    setSearch("");
    setStatus("");
    setCustomerId("");
    setPage(1);
  }

  function handleSearch(value) {
    setSearch(value);
    setPage(1);
  }

  function handleStatus(event) {
    setStatus(event.target.value);
    setPage(1);
  }

  function handleCustomer(event) {
    setCustomerId(event.target.value);
    setPage(1);
  }

  function renderResults() {
    if (invoicesState.error) {
      return <ErrorState message={invoicesState.error.message} onRetry={invoicesState.refresh} />;
    }
    if (!invoicesState.data) {
      return <LoadingState />;
    }

    const { items, total } = invoicesState.data;

    if (items.length === 0) {
      return filtersActive ? (
        <EmptyState
          title="No matching invoices"
          message="Try a different search or clear the filters."
          action={
            <Button variant="secondary" onClick={clearFilters}>
              Clear filters
            </Button>
          }
        />
      ) : (
        <EmptyState
          icon={FileText}
          title="No invoices yet"
          message="Invoices you create will appear here with their due dates and payment status."
          action={
            <Link to="/invoices/new" className={PRIMARY_LINK}>
              <FilePlus className="h-4 w-4" aria-hidden="true" />
              Create invoice
            </Link>
          }
        />
      );
    }

    return (
      <div className="space-y-4">
        <div className={`${CARD} hidden overflow-x-auto md:block`}>
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th scope="col" className="px-4 py-3 font-medium">Invoice</th>
                <th scope="col" className="px-4 py-3 font-medium">Customer</th>
                <th scope="col" className="px-4 py-3 font-medium">Description</th>
                <th scope="col" className="px-4 py-3 font-medium">Due</th>
                <th scope="col" className="px-4 py-3 text-right font-medium">Total</th>
                <th scope="col" className="px-4 py-3 text-right font-medium">Paid</th>
                <th scope="col" className="px-4 py-3 text-right font-medium">Outstanding</th>
                <th scope="col" className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((invoice) => (
                <tr key={invoice.id}>
                  <td className="px-4 py-3 font-medium">
                    <Link to={`/invoices/${invoice.id}`} className="text-brand-700 hover:underline">
                      {invoice.invoice_number}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{invoice.customer_name}</td>
                  <td className="px-4 py-3 text-slate-700">{invoice.description}</td>
                  <td className="px-4 py-3 text-slate-700">{formatDate(invoice.due_date)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{formatPaiseToRupees(invoice.total_paise)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{formatPaiseToRupees(invoice.paid_paise)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {formatPaiseToRupees(invoice.outstanding_paise)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge kind="invoice" value={invoice.status} />
                      <OverdueNote invoice={invoice} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <ul className="space-y-3 md:hidden">
          {items.map((invoice) => (
            <li key={invoice.id} className={`${CARD} p-4`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <Link to={`/invoices/${invoice.id}`} className="font-medium text-brand-700 hover:underline">
                    {invoice.invoice_number}
                  </Link>
                  <p className="text-sm text-slate-600">{invoice.customer_name}</p>
                </div>
                <StatusBadge kind="invoice" value={invoice.status} />
              </div>
              <p className="mt-2 text-sm text-slate-700">{invoice.description}</p>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <dt className="text-slate-500">Due</dt>
                  <dd className="text-slate-900">{formatDate(invoice.due_date)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Total</dt>
                  <dd className="tabular-nums text-slate-900">{formatPaiseToRupees(invoice.total_paise)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Paid</dt>
                  <dd className="tabular-nums text-slate-900">{formatPaiseToRupees(invoice.paid_paise)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Outstanding</dt>
                  <dd className="tabular-nums text-slate-900">
                    {formatPaiseToRupees(invoice.outstanding_paise)}
                  </dd>
                </div>
              </dl>
              <div className="mt-2">
                <OverdueNote invoice={invoice} />
              </div>
            </li>
          ))}
        </ul>

        <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Invoices"
        description="Every invoice, its payment status and what is still due."
        actions={
          <Link to="/invoices/new" className={PRIMARY_LINK}>
            <FilePlus className="h-4 w-4" aria-hidden="true" />
            Create invoice
          </Link>
        }
      />

      <div className="mb-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111827] p-4 shadow-2xs">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-12 items-end">
          <div className="sm:col-span-2 lg:col-span-6 space-y-1">
            <label
              htmlFor="invoice-search-input"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Search
            </label>
            <SearchInput
              id="invoice-search-input"
              value={search}
              onChange={handleSearch}
              placeholder="Search by invoice #, customer, or description…"
            />
          </div>
          <div className="lg:col-span-3">
            <Select id="invoice-status-filter" label="Status" value={status} onChange={handleStatus}>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="lg:col-span-3">
            <Select
              id="invoice-customer-filter"
              label="Customer"
              value={customerId}
              onChange={handleCustomer}
              error={customersState.error ? "Customers could not be loaded." : undefined}
            >
              <option value="">All customers</option>
              {customers.map((customer) => (
                <option key={customer.id} value={String(customer.id)}>
                  {customer.name}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </div>

      {renderResults()}
    </div>
  );
}

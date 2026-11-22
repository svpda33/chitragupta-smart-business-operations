import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, UserPlus, Users } from "lucide-react";
import Button from "../components/common/Button.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import Pagination from "../components/common/Pagination.jsx";
import SearchInput from "../components/common/SearchInput.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useDebouncedValue } from "../hooks/useDebouncedValue.js";
import { listCustomers } from "../services/customerService.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";

const PAGE_SIZE = 20;

const ADD_BUTTON_CLASSES =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";

function orDash(value) {
  return typeof value === "string" && value.trim() !== "" ? value : "—";
}

function CardField({ label, value }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-0.5 break-words text-slate-900">{value}</dd>
    </div>
  );
}

export default function CustomersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search, 300);
  const query = debouncedSearch.trim();

  const { data, error, loading, refresh } = useAsync(
    () => listCustomers({ page, page_size: PAGE_SIZE, search: query }),
    [page, query]
  );

  const handleSearchChange = (value) => {
    setSearch(value);
    setPage(1);
  };

  const customers = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasSearch = query !== "";

  let content;
  if (error) {
    content = <ErrorState message={error.message} onRetry={refresh} />;
  } else if (loading && !data) {
    content = <LoadingState />;
  } else if (total === 0 && !hasSearch) {
    content = (
      <EmptyState
        icon={Users}
        title="No customers yet"
        message="Add your first customer to start tracking what they owe you."
        action={
          <Link to="/customers/new" className={ADD_BUTTON_CLASSES}>
            <UserPlus className="h-4 w-4" aria-hidden="true" />
            Add customer
          </Link>
        }
      />
    );
  } else if (total === 0) {
    content = (
      <EmptyState
        icon={Search}
        title="No matching customers"
        message="Try a different name, email or phone number."
        action={
          <Button variant="secondary" onClick={() => handleSearchChange("")}>
            Clear search
          </Button>
        }
      />
    );
  } else {
    content = (
      <>
        <div className="hidden overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm md:block">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                  Name
                </th>
                <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                  Email
                </th>
                <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600">
                  Phone
                </th>
                <th scope="col" className="px-4 py-3 text-right font-medium text-slate-600">
                  Invoices
                </th>
                <th scope="col" className="px-4 py-3 text-right font-medium text-slate-600">
                  Outstanding
                </th>
                <th scope="col" className="px-4 py-3 text-right font-medium text-slate-600">
                  Overdue
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {customers.map((customer) => (
                <tr key={customer.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/customers/${customer.id}`}
                      className="font-medium text-brand-700 hover:underline"
                    >
                      {customer.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{orDash(customer.email)}</td>
                  <td className="px-4 py-3 text-slate-700">{orDash(customer.phone)}</td>
                  <td className="px-4 py-3 text-right text-slate-700">{customer.invoice_count}</td>
                  <td className="px-4 py-3 text-right text-slate-700">
                    {formatPaiseToRupees(customer.outstanding_paise)}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700">
                    {formatPaiseToRupees(customer.overdue_paise)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <ul className="space-y-3 md:hidden">
          {customers.map((customer) => (
            <li
              key={customer.id}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <Link
                to={`/customers/${customer.id}`}
                className="font-medium text-brand-700 hover:underline"
              >
                {customer.name}
              </Link>
              <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                <CardField label="Email" value={orDash(customer.email)} />
                <CardField label="Phone" value={orDash(customer.phone)} />
                <CardField label="Invoices" value={customer.invoice_count} />
                <CardField label="Outstanding" value={formatPaiseToRupees(customer.outstanding_paise)} />
                <CardField label="Overdue" value={formatPaiseToRupees(customer.overdue_paise)} />
              </dl>
            </li>
          ))}
        </ul>

        <div className="mt-4">
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={setPage}
          />
        </div>
      </>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        description="The people who owe your business money, and what they owe."
        actions={
          <Link to="/customers/new" className={ADD_BUTTON_CLASSES}>
            <UserPlus className="h-4 w-4" aria-hidden="true" />
            Add customer
          </Link>
        }
      />

      <div className="max-w-md">
        <SearchInput
          value={search}
          onChange={handleSearchChange}
          placeholder="Search by name, email or phone"
        />
      </div>

      {content}
    </div>
  );
}

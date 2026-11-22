const INVOICE_STATUS = {
  draft: {
    label: "Draft",
    classes: "bg-slate-100 text-slate-700 ring-1 ring-slate-200/80 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700",
  },
  pending: {
    label: "Pending",
    classes: "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200/80 dark:bg-indigo-500/15 dark:text-indigo-300 dark:ring-indigo-500/30",
  },
  partially_paid: {
    label: "Partly paid",
    classes: "bg-blue-50 text-blue-700 ring-1 ring-blue-200/80 dark:bg-blue-500/15 dark:text-blue-300 dark:ring-blue-500/30",
  },
  overdue: {
    label: "Overdue",
    classes: "bg-red-50 text-red-700 ring-1 ring-red-200/80 dark:bg-red-500/15 dark:text-red-300 dark:ring-red-500/30",
  },
  paid: {
    label: "Paid",
    classes: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:ring-emerald-500/30",
  },
};

const PAYMENT_STATUS = {
  active: {
    label: "Active",
    classes: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200/80 dark:bg-emerald-500/15 dark:text-emerald-300 dark:ring-emerald-500/30",
  },
  reversed: {
    label: "Reversed",
    classes: "bg-slate-100 text-slate-600 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:ring-slate-700",
  },
};

const KINDS = {
  invoice: INVOICE_STATUS,
  payment: PAYMENT_STATUS,
};

export default function StatusBadge({ kind, value }) {
  const map = KINDS[kind] ?? {};
  const entry = map[value] ?? {
    label: String(value ?? "—"),
    classes: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${entry.classes}`}
    >
      {entry.label}
    </span>
  );
}

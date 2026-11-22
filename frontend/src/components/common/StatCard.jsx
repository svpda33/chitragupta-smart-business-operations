export default function StatCard({
  label,
  value = "No data yet",
  note,
  icon: Icon,
  tone = "default",
}) {
  const toneIconBg = {
    default: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
    brand: "bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300",
    danger: "bg-red-50 text-red-600 dark:bg-red-500/15 dark:text-red-300",
    success: "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300",
    warning: "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300",
  }[tone] ?? "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-2xs transition-colors hover:border-slate-300 dark:border-slate-800 dark:bg-[#111827] dark:hover:border-slate-700">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </p>
        {Icon && (
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${toneIconBg}`}>
            <Icon className="h-4 w-4" aria-hidden="true" />
          </div>
        )}
      </div>
      <p className="mt-2.5 text-2xl font-bold tracking-tight tabular-nums text-slate-900 dark:text-slate-100">
        {value}
      </p>
      {note && <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">{note}</p>}
    </div>
  );
}

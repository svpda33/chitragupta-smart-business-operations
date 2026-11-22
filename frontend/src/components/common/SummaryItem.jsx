const VALUE_TONES = {
  danger: "text-red-600 dark:text-red-400",
  success: "text-emerald-600 dark:text-emerald-400",
  warning: "text-amber-600 dark:text-amber-400",
};

export default function SummaryItem({ label, value, tone }) {
  const valueTone = VALUE_TONES[tone] ?? "text-slate-900 dark:text-slate-100";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-800 dark:bg-[#111827]">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
        {label}
      </p>
      <p className={`mt-1.5 text-xl font-bold tracking-tight tabular-nums ${valueTone}`}>{value}</p>
    </div>
  );
}

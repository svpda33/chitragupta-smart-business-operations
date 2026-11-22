export default function Select({
  id,
  label,
  error,
  hint,
  options,
  className = "",
  children,
  ...rest
}) {
  const errorId = id ? `${id}-error` : undefined;
  const hintId = id ? `${id}-hint` : undefined;
  const describedBy = error ? errorId : hint ? hintId : undefined;

  return (
    <div className="space-y-1">
      {label ? (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          {label}
        </label>
      ) : null}
      <select
        id={id}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy}
        className={`block min-h-[40px] w-full rounded-xl border bg-white px-3.5 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-100 disabled:text-slate-500 dark:bg-slate-900/70 dark:text-slate-100 dark:disabled:bg-slate-800 ${
          error ? "border-red-500 dark:border-red-500" : "border-slate-300 dark:border-slate-700"
        } ${className}`}
        {...rest}
      >
        {Array.isArray(options)
          ? options.map((opt) => (
              <option key={String(opt.value)} value={opt.value}>
                {opt.label}
              </option>
            ))
          : children}
      </select>
      {error ? (
        <p id={errorId} className="text-xs text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : hint ? (
        <p id={hintId} className="text-xs text-slate-500 dark:text-slate-400">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

import { Loader2 } from "lucide-react";

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 " +
  "disabled:cursor-not-allowed disabled:opacity-60";

const VARIANTS = {
  primary: "bg-brand-600 text-white shadow-2xs hover:bg-brand-700 dark:bg-brand-600 dark:hover:bg-brand-500",
  secondary:
    "border border-slate-200 bg-white text-slate-700 shadow-2xs hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
  danger: "bg-red-600 text-white shadow-2xs hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-500",
  ghost:
    "bg-transparent text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
};

export default function Button({
  variant = "primary",
  type = "button",
  disabled,
  loading,
  onClick,
  children,
  className = "",
  ...rest
}) {
  const variantClasses = VARIANTS[variant] ?? VARIANTS.primary;
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      onClick={onClick}
      className={`${BASE} ${variantClasses} ${className}`}
      {...rest}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}

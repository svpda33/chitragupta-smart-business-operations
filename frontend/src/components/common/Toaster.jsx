import { AlertTriangle, CheckCircle, Info, X } from "lucide-react";

const TONES = {
  success: {
    label: "Success",
    icon: CheckCircle,
    classes: "border-emerald-200 bg-emerald-50 text-emerald-900",
    iconClasses: "text-emerald-600",
  },
  error: {
    label: "Error",
    icon: AlertTriangle,
    classes: "border-red-200 bg-red-50 text-red-900",
    iconClasses: "text-red-600",
  },
  info: {
    label: "Info",
    icon: Info,
    classes: "border-slate-200 bg-white text-slate-900",
    iconClasses: "text-brand-600",
  },
};

export default function Toaster({ toasts, onDismiss }) {
  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3">
      {toasts.map((toast) => {
        const tone = TONES[toast.type] ?? TONES.info;
        const Icon = tone.icon;
        return (
          <div
            key={toast.id}
            role="status"
            aria-live="polite"
            className={`pointer-events-auto flex items-start gap-3 rounded-lg border p-4 shadow-lg ${tone.classes}`}
          >
            <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${tone.iconClasses}`} aria-hidden="true" />
            <div className="flex-1 text-sm">
              <p className="font-semibold">{tone.label}</p>
              <p>{toast.message}</p>
            </div>
            <button
              type="button"
              aria-label="Dismiss notification"
              onClick={() => onDismiss(toast.id)}
              className="rounded p-1 text-slate-500 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </div>
  );
}

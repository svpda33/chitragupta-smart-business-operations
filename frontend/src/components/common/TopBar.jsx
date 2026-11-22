import { LogOut, Menu, Monitor, Moon, Sun } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import useHealth from "../../hooks/useHealth.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { useTheme } from "../../context/ThemeContext.jsx";

const PAGE_TITLES = {
  "/dashboard": "Financial Overview",
  "/catalogue": "Products & Services Catalogue",
  "/inventory": "Inventory & Stock Ledger",
  "/notepad": "Business Notepad",
  "/customers": "Customers",
  "/invoices": "Invoices",
  "/payments": "Payments",
  "/cash-flow": "Cash Flow & Forecasting",
  "/reminders": "Payment Reminders",
  "/ai-assistant": "AI Finance Copilot",
  "/settings": "Business Settings",
};

const THEME_OPTIONS = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

function resolvePageTitle(pathname) {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  if (pathname.startsWith("/customers")) return "Customers";
  if (pathname.startsWith("/invoices")) return "Invoices";
  if (pathname.startsWith("/payments")) return "Payments";
  if (pathname.startsWith("/catalogue")) return "Catalogue";
  if (pathname.startsWith("/inventory")) return "Inventory";
  if (pathname.startsWith("/notepad")) return "Notepad";
  if (pathname.startsWith("/cash-flow")) return "Cash Flow";
  if (pathname.startsWith("/reminders")) return "Reminders";
  if (pathname.startsWith("/ai-assistant")) return "AI Finance Copilot";
  if (pathname.startsWith("/settings")) return "Settings";
  return "Chitragupta";
}

function HealthIndicator() {
  const { status } = useHealth();

  if (status === "ok") {
    return (
      <span className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300 sm:inline-flex">
        <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
        Connected
      </span>
    );
  }

  if (status === "error") {
    return (
      <span className="hidden items-center gap-2 rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300 sm:inline-flex">
        <span className="h-2 w-2 rounded-full bg-red-500" aria-hidden="true" />
        Backend offline
      </span>
    );
  }

  return (
    <span className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 sm:inline-flex">
      <span className="h-2 w-2 rounded-full bg-slate-400" aria-hidden="true" />
      Checking…
    </span>
  );
}

function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <div
      role="group"
      aria-label="Theme selector"
      className="inline-flex items-center rounded-xl border border-slate-200 bg-slate-100/80 p-0.5 dark:border-slate-700 dark:bg-slate-800/80"
    >
      {THEME_OPTIONS.map(({ value, label, icon: Icon }) => {
        const active = theme === value;
        return (
          <button
            key={value}
            type="button"
            onClick={() => setTheme(value)}
            aria-pressed={active}
            title={`${label} theme`}
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
              active
                ? "bg-white text-slate-900 shadow-xs dark:bg-slate-900 dark:text-brand-300"
                : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            }`}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="hidden md:inline">{label}</span>
          </button>
        );
      })}
    </div>
  );
}

export default function TopBar({ onMenuClick }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const title = resolvePageTitle(pathname);

  async function handleSignOut() {
    await logout();
    navigate("/", { replace: true });
  }

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur-md dark:border-slate-800 dark:bg-[#111827]/90">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Open navigation"
          className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 lg:hidden"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>

        <div className="min-w-0 flex-1">
          <h1 className="truncate font-display text-base font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {title}
          </h1>
        </div>

        <div className="flex items-center gap-2.5 sm:gap-3">
          <ThemeSwitcher />
          <HealthIndicator />
          {user && (
            <button
              type="button"
              onClick={handleSignOut}
              title={`Sign out (${user.email})`}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2.5 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 dark:hover:bg-rose-950/50 dark:hover:text-rose-300 transition-colors"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

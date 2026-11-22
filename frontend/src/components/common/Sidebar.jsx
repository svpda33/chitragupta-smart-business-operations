import { NavLink } from "react-router-dom";
import {
  Bell,
  Boxes,
  ChevronLeft,
  ChevronRight,
  FileText,
  LayoutDashboard,
  Package,
  Settings,
  Sparkles,
  StickyNote,
  TrendingUp,
  Users,
  Wallet,
  X,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext.jsx";

const NAV_SECTIONS = [
  {
    title: "Overview",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
      { to: "/cash-flow", label: "Cash Flow", icon: TrendingUp },
      { to: "/ai-assistant", label: "AI Assistant", icon: Sparkles, badge: "AI" },
    ],
  },
  {
    title: "Sales & Billing",
    items: [
      { to: "/customers", label: "Customers", icon: Users },
      { to: "/invoices", label: "Invoices", icon: FileText },
      { to: "/payments", label: "Payments", icon: Wallet },
      { to: "/reminders", label: "Reminders", icon: Bell },
    ],
  },
  {
    title: "Products & Stock",
    items: [
      { to: "/catalogue", label: "Catalogue", icon: Package },
      { to: "/inventory", label: "Inventory", icon: Boxes },
    ],
  },
  {
    title: "Workspace",
    items: [
      { to: "/notepad", label: "Notepad", icon: StickyNote },
      { to: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

function BrandMark({ business }) {
  if (business?.logo_url) {
    return (
      <img
        src={business.logo_url}
        alt={business.name || "Business logo"}
        className="h-9 w-9 shrink-0 rounded-xl object-cover border border-slate-200 dark:border-slate-700 bg-white shadow-sm"
      />
    );
  }
  const initials = (business?.name || "CG")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
  return (
    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-xs font-extrabold text-white shadow-sm">
      {initials || "CG"}
    </div>
  );
}

export default function Sidebar({
  mobileOpen,
  onMobileClose,
  collapsed,
  onToggleCollapse,
}) {
  const { business } = useAuth();
  const handleNavClick = () => {
    if (mobileOpen) onMobileClose();
  };

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          aria-hidden="true"
          onClick={onMobileClose}
          className="fixed inset-0 z-30 bg-slate-950/50 backdrop-blur-[1px] transition-opacity lg:hidden"
        />
      )}

      <aside
        aria-label="Sidebar"
        className={`fixed inset-y-0 left-0 z-40 flex flex-col border-r border-slate-200 bg-white transition-all duration-200 ease-out dark:border-slate-800 dark:bg-[#111827] ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } w-64 lg:translate-x-0 ${collapsed ? "lg:w-[72px]" : "lg:w-64"}`}
      >
        {/* Brand Header */}
        <div
          className={`flex h-16 items-center border-b border-slate-200 dark:border-slate-800 ${
            collapsed ? "justify-center px-2" : "justify-between px-4"
          }`}
        >
          <div className={`flex items-center gap-3 overflow-hidden ${collapsed ? "lg:justify-center" : ""}`}>
            <BrandMark business={business} />
            <div className={`min-w-0 transition-opacity duration-150 ${collapsed ? "lg:hidden" : "block"}`}>
              <p className="truncate font-display text-sm font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                {business?.name || "Chitragupta"}
              </p>
              <p className="truncate text-[10px] font-medium text-slate-500 dark:text-slate-400">
                Powered by Chitragupta
              </p>
            </div>
          </div>

          {/* Mobile close button */}
          <button
            type="button"
            onClick={onMobileClose}
            aria-label="Close navigation"
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100 lg:hidden"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav aria-label="Main navigation" className="flex-1 space-y-5 overflow-y-auto px-2.5 py-4">
          {NAV_SECTIONS.map((section) => (
            <div key={section.title}>
              <p
                className={`mb-1.5 px-2.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 ${
                  collapsed ? "lg:hidden" : "block"
                }`}
              >
                {section.title}
              </p>
              <ul className="space-y-1">
                {section.items.map(({ to, label, icon: Icon, end, badge }) => (
                  <li key={to} className="group relative">
                    <NavLink
                      to={to}
                      end={end}
                      onClick={handleNavClick}
                      title={collapsed ? label : undefined}
                      className={({ isActive }) =>
                        `flex items-center rounded-xl text-sm font-medium transition-colors ${
                          collapsed
                            ? "lg:justify-center lg:px-0 lg:py-2.5 gap-3 px-3 py-2.5"
                            : "gap-3 px-3 py-2.5"
                        } ${
                          isActive
                            ? "bg-brand-50 text-brand-700 shadow-2xs ring-1 ring-brand-200/70 dark:bg-brand-500/15 dark:text-brand-300 dark:ring-brand-500/30"
                            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/70 dark:hover:text-slate-100"
                        }`
                      }
                    >
                      <Icon className="h-[18px] w-[18px] shrink-0" aria-hidden="true" />
                      <span className={`flex-1 truncate ${collapsed ? "lg:hidden" : "block"}`}>
                        {label}
                      </span>
                      {badge && (
                        <span
                          className={`rounded-md bg-brand-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white ${
                            collapsed ? "lg:hidden" : "inline-flex"
                          }`}
                        >
                          {badge}
                        </span>
                      )}
                    </NavLink>

                    {/* Floating Tooltip when Desktop Sidebar is Collapsed */}
                    {collapsed && (
                      <div
                        role="tooltip"
                        className="pointer-events-none fixed left-[76px] z-50 hidden -translate-y-8 whitespace-nowrap rounded-lg bg-slate-900 px-2.5 py-1.5 text-xs font-medium text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100 dark:bg-slate-800 lg:block"
                      >
                        {label}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {/* Desktop Sidebar Collapse Toggle (Dedicated separate control) */}
        <div className="hidden border-t border-slate-200 p-2.5 dark:border-slate-800 lg:block">
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={`flex w-full items-center rounded-xl py-2 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100 ${
              collapsed ? "justify-center px-0" : "justify-between px-3"
            }`}
          >
            {!collapsed && <span>Collapse sidebar</span>}
            {collapsed ? (
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            ) : (
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        </div>
      </aside>
    </>
  );
}

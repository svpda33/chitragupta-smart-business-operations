import { Link } from "react-router-dom";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bell,
  CheckCircle2,
  Clock,
  FilePlus,
  Info,
  Landmark,
  Receipt,
  Sparkles,
  TrendingUp,
  Wallet,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import PageHeader from "../components/common/PageHeader.jsx";
import StatCard from "../components/common/StatCard.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import StatusBadge from "../components/common/StatusBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { getDashboard } from "../services/dashboardService.js";
import { formatDate } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";

const CARD =
  "rounded-2xl border border-slate-200 bg-white p-5 shadow-2xs dark:border-slate-800 dark:bg-[#111827]";
const AGEING_COLORS = ["#0d9488", "#f59e0b", "#f97316", "#ef4444", "#991b1b"];
const STATUS_COLORS = {
  pending: "#3b82f6",
  overdue: "#ef4444",
  paid: "#10b981",
  draft: "#64748b",
};

export default function DashboardPage() {
  const { business } = useAuth();
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  const { data: dashboard, loading, error, refresh } = useAsync(getDashboard, []);

  if (loading && !dashboard) return <LoadingState label="Loading financial dashboard…" />;
  if (error) return <ErrorState message={error.message} onRetry={refresh} />;
  if (!dashboard) return null;

  const {
    total_outstanding_paise,
    total_overdue_paise,
    overdue_invoices_count,
    pending_invoices_count,
    draft_invoices_count,
    cash_on_hand_paise,
    safety_cash_threshold_paise,
    runway_days,
    total_invoiced_month_paise,
    total_collected_month_paise,
    total_invoiced_all_time_paise,
    total_collected_all_time_paise,
    collection_efficiency_percent,
    status_distribution = [],
    ageing_breakdown = [],
    actionable_alerts = [],
    recent_invoices = [],
    recent_payments = [],
  } = dashboard;

  const gridStroke = isDark ? "#1e293b" : "#f1f5f9";
  const axisTickColor = isDark ? "#94a3b8" : "#64748b";
  const tooltipStyle = {
    backgroundColor: isDark ? "#0f172a" : "#ffffff",
    borderColor: isDark ? "#334155" : "#e2e8f0",
    color: isDark ? "#f1f5f9" : "#0f172a",
    borderRadius: "12px",
    fontSize: "12px",
  };

  const ageingChartData = ageing_breakdown.map((b) => ({
    name: b.label.split(" ")[0],
    fullName: b.label,
    amountRupees: Math.round(b.amount_paise / 100),
    count: b.count,
  }));

  const pieChartData = status_distribution
    .filter((s) => s.amount_paise > 0 || s.count > 0)
    .map((s) => ({
      name: s.label,
      value: Math.round(s.amount_paise / 100),
      count: s.count,
      status: s.status,
    }));

  return (
    <div className="space-y-6">
      <PageHeader
        title={
          <span className="inline-flex items-center gap-3">
            {business?.logo_url && (
              <img
                src={business.logo_url}
                alt={business.name || "Business Logo"}
                className="h-9 w-9 rounded-xl object-cover border border-slate-200 dark:border-slate-700 bg-white shadow-xs"
              />
            )}
            <span>
              {business?.name ? `${business.name} — Financial Overview` : "Financial Overview"}
            </span>
          </span>
        }
        description="Live ledger position, collection velocity, overdue risk, stock alerts, and cash runway."
        actions={
          <>
            <Link
              to="/ai-assistant"
              className="inline-flex items-center gap-1.5 rounded-xl border border-brand-200 bg-brand-50 px-3.5 py-2 text-sm font-medium text-brand-700 transition-colors hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/15 dark:text-brand-300 dark:hover:bg-brand-500/25"
            >
              <Sparkles className="h-4 w-4" />
              Ask Copilot
            </Link>
            <Link
              to="/payments/new"
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 shadow-2xs transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              <Wallet className="h-4 w-4" />
              Record Payment
            </Link>
            <Link
              to="/invoices/new"
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-3.5 py-2 text-sm font-medium text-white shadow-2xs transition-colors hover:bg-brand-700"
            >
              <FilePlus className="h-4 w-4" />
              New Invoice
            </Link>
          </>
        }
      />

      {/* Clean-Start Quick Onboarding Actions for brand-new accounts */}
      {recent_invoices.length === 0 && (
        <div className="rounded-2xl border border-brand-200/80 dark:border-brand-800/60 bg-gradient-to-r from-brand-50/80 via-white to-emerald-50/60 dark:from-brand-950/40 dark:via-[#111827] dark:to-emerald-950/30 p-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="font-display text-base font-bold text-slate-900 dark:text-white">
                Welcome to {business?.name || "your workspace"} — ready for your first real transaction
              </p>
              <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                Your account starts 100% clean. Add your first customer or product/service to begin
                billing and tracking stock.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                to="/customers/new"
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                + Add Customer
              </Link>
              <Link
                to="/catalogue"
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                + Add Product / Service
              </Link>
              <Link
                to="/notepad"
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                Open Notepad
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Primary KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total Outstanding"
          value={formatPaiseToRupees(total_outstanding_paise)}
          note={`${pending_invoices_count + overdue_invoices_count} unpaid sent invoices`}
          icon={Receipt}
          tone="brand"
        />
        <StatCard
          label="Total Overdue"
          value={formatPaiseToRupees(total_overdue_paise)}
          note={
            overdue_invoices_count > 0
              ? `${overdue_invoices_count} overdue invoice(s) need follow-up`
              : "All invoices on schedule"
          }
          icon={Clock}
          tone={overdue_invoices_count > 0 ? "danger" : "success"}
        />
        <StatCard
          label="Estimated Cash on Hand"
          value={formatPaiseToRupees(cash_on_hand_paise)}
          note={`Runway ~${runway_days} days • ${
            cash_on_hand_paise < safety_cash_threshold_paise ? "Below safety reserve" : "Above safety reserve"
          }`}
          icon={Landmark}
          tone={cash_on_hand_paise < safety_cash_threshold_paise ? "warning" : "success"}
        />
        <StatCard
          label="Collected All-Time"
          value={formatPaiseToRupees(total_collected_all_time_paise)}
          note={`Collection efficiency: ${collection_efficiency_percent}% of billed`}
          icon={TrendingUp}
          tone="default"
        />
      </div>

      {/* Monthly Cash vs Invoiced Strip */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-emerald-200/80 bg-emerald-50/50 p-4 dark:border-emerald-500/25 dark:bg-emerald-500/10">
          <div className="text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
            Collected This Month
          </div>
          <div className="mt-1.5 text-2xl font-bold tabular-nums text-emerald-900 dark:text-emerald-100">
            {formatPaiseToRupees(total_collected_month_paise)}
          </div>
          <div className="mt-1 text-xs text-emerald-700/90 dark:text-emerald-300/80">
            Actual cash received (bank / UPI / cash)
          </div>
        </div>
        <div className="rounded-2xl border border-blue-200/80 bg-blue-50/50 p-4 dark:border-blue-500/25 dark:bg-blue-500/10">
          <div className="text-xs font-semibold uppercase tracking-wider text-blue-700 dark:text-blue-300">
            Invoiced This Month
          </div>
          <div className="mt-1.5 text-2xl font-bold tabular-nums text-blue-900 dark:text-blue-100">
            {formatPaiseToRupees(total_invoiced_month_paise)}
          </div>
          <div className="mt-1 text-xs text-blue-700/90 dark:text-blue-300/80">
            Sent invoices billed in the current month
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-[#111827]">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Total Billed All-Time
          </div>
          <div className="mt-1.5 text-2xl font-bold tabular-nums text-slate-900 dark:text-slate-100">
            {formatPaiseToRupees(total_invoiced_all_time_paise)}
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {draft_invoices_count} draft invoice{draft_invoices_count === 1 ? "" : "s"} awaiting dispatch
          </div>
        </div>
      </div>

      {/* Actionable Business Alerts */}
      {actionable_alerts.length > 0 && (
        <section aria-labelledby="alerts-heading" className="space-y-3">
          <div className="flex items-center justify-between">
            <h2
              id="alerts-heading"
              className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
            >
              <Bell className="h-4 w-4 text-brand-600 dark:text-brand-400" />
              Actionable Business Alerts
            </h2>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              {actionable_alerts.length} active alert{actionable_alerts.length > 1 ? "s" : ""}
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {actionable_alerts.map((alert) => {
              const isDanger = alert.type === "danger";
              const isWarning = alert.type === "warning";
              const isSuccess = alert.type === "success";

              const boxStyle = isDanger
                ? "border-red-200 bg-red-50/60 dark:border-red-500/30 dark:bg-red-500/10"
                : isWarning
                ? "border-amber-200 bg-amber-50/60 dark:border-amber-500/30 dark:bg-amber-500/10"
                : isSuccess
                ? "border-emerald-200 bg-emerald-50/60 dark:border-emerald-500/30 dark:bg-emerald-500/10"
                : "border-blue-200 bg-blue-50/60 dark:border-blue-500/30 dark:bg-blue-500/10";

              const IconComponent = isDanger
                ? AlertCircle
                : isWarning
                ? AlertTriangle
                : isSuccess
                ? CheckCircle2
                : Info;

              const iconColor = isDanger
                ? "text-red-600 dark:text-red-400"
                : isWarning
                ? "text-amber-600 dark:text-amber-400"
                : isSuccess
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-blue-600 dark:text-blue-400";

              return (
                <div
                  key={alert.id}
                  className={`flex flex-col justify-between rounded-2xl border p-4 ${boxStyle}`}
                >
                  <div className="flex items-start gap-3">
                    <IconComponent className={`mt-0.5 h-5 w-5 shrink-0 ${iconColor}`} />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {alert.title}
                        </h3>
                        <span className="rounded-md border border-slate-200/80 bg-white/80 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-700 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-300">
                          {alert.priority}
                        </span>
                      </div>
                      <p className="mt-1 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                        {alert.message}
                      </p>
                    </div>
                  </div>

                  {alert.action_url && (
                    <div className="mt-3 flex justify-end border-t border-slate-200/60 pt-2.5 dark:border-slate-700/50">
                      <Link
                        to={alert.action_url}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:underline dark:text-brand-300"
                      >
                        {alert.action_label || "Take action"}
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className={CARD}>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                Receivables Ageing Breakdown
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Outstanding balances grouped by overdue age
              </p>
            </div>
            <Link
              to="/reminders"
              className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400"
            >
              Chase overdue →
            </Link>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ageingChartData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridStroke} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: axisTickColor }} />
                <YAxis
                  tick={{ fontSize: 11, fill: axisTickColor }}
                  tickFormatter={(val) => (val >= 1000 ? `₹${val / 1000}k` : `₹${val}`)}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(val, _name, item) => [
                    `₹${val.toLocaleString("en-IN")}`,
                    `${item.payload.fullName} (${item.payload.count} inv)`,
                  ]}
                />
                <Bar dataKey="amountRupees" radius={[6, 6, 0, 0]}>
                  {ageingChartData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={AGEING_COLORS[index % AGEING_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={CARD}>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                Invoice Pipeline & Collections
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Proportional breakdown of pending, overdue, and collected amounts
              </p>
            </div>
            <Link
              to="/invoices"
              className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400"
            >
              All invoices →
            </Link>
          </div>

          <div className="flex h-64 w-full items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={62}
                  outerRadius={88}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieChartData.map((entry, index) => (
                    <Cell
                      key={`pie-cell-${index}`}
                      fill={STATUS_COLORS[entry.status] || "#94a3b8"}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(val, _name, item) => [
                    `₹${val.toLocaleString("en-IN")}`,
                    `${item.payload.name} (${item.payload.count} invoices)`,
                  ]}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: "12px" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className={`${CARD} overflow-hidden`}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Recent Invoices
            </h3>
            <Link
              to="/invoices"
              className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400"
            >
              View all
            </Link>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {recent_invoices.slice(0, 5).map((inv) => (
              <div key={inv.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/invoices/${inv.id}`}
                      className="truncate text-sm font-semibold text-slate-900 hover:text-brand-600 dark:text-slate-100 dark:hover:text-brand-400"
                    >
                      {inv.invoice_number}
                    </Link>
                    <StatusBadge kind="invoice" value={inv.status} />
                  </div>
                  <div className="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">
                    {inv.customer_name}
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <div className="text-sm font-semibold tabular-nums text-slate-900 dark:text-slate-100">
                    {formatPaiseToRupees(inv.total_paise)}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    Due {formatDate(inv.due_date)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={`${CARD} overflow-hidden`}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Recent Payments Received
            </h3>
            <Link
              to="/payments"
              className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400"
            >
              View all
            </Link>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {recent_payments.slice(0, 5).map((pmt) => (
              <div key={pmt.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {pmt.customer_name}
                  </div>
                  <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <span>{formatDate(pmt.payment_date)}</span>
                    <span>•</span>
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase dark:bg-slate-800 dark:text-slate-300">
                      {pmt.method}
                    </span>
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <div
                    className={`text-sm font-semibold tabular-nums ${
                      pmt.status === "reversed"
                        ? "text-slate-400 line-through"
                        : "text-emerald-600 dark:text-emerald-400"
                    }`}
                  >
                    {formatPaiseToRupees(pmt.amount_paise)}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    {pmt.status === "reversed" ? "Reversed" : "Credited"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  DollarSign,
  HelpCircle,
  Plus,
  RefreshCw,
  Sliders,
  Trash2,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Button from "../components/common/Button.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import Input from "../components/common/Input.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import Modal from "../components/common/Modal.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import Select from "../components/common/Select.jsx";
import SummaryItem from "../components/common/SummaryItem.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useTheme } from "../context/ThemeContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { getCashFlowForecast, simulateCashFlow } from "../services/cashflowService.js";
import { createExpense, deleteExpense, listExpenses } from "../services/expenseService.js";
import { formatDate, todayIso } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";
import { validateRupeeInput } from "../utils/money.js";

const CARD =
  "rounded-2xl border border-slate-200 bg-white p-5 shadow-2xs dark:border-slate-800 dark:bg-[#111827]";
const HORIZON_OPTIONS = [
  { value: 30, label: "Next 30 Days" },
  { value: 60, label: "Next 60 Days" },
  { value: 90, label: "Next 90 Days" },
];

const EXPENSE_CATEGORIES = [
  { value: "Rent", label: "Rent & Office" },
  { value: "Payroll", label: "Salaries / Assistant Stipend" },
  { value: "Software", label: "SaaS & Subscriptions" },
  { value: "Utilities", label: "Internet & Utilities" },
  { value: "Taxes", label: "Taxes & Compliance" },
  { value: "Equipment", label: "Equipment & Hardware" },
  { value: "Other", label: "Other Operating Expense" },
];

export default function CashFlowPage() {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  const [horizon, setHorizon] = useState(30);
  const [delayDays, setDelayDays] = useState(0);
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const showToast = useToast();

  // Add Expense Modal state
  const [expenseModalOpen, setExpenseModalOpen] = useState(false);
  const [expenseName, setExpenseName] = useState("");
  const [expenseCategory, setExpenseCategory] = useState("Rent");
  const [expenseAmount, setExpenseAmount] = useState("");
  const [expenseDate, setExpenseDate] = useState(todayIso());
  const [expenseRecurring, setExpenseRecurring] = useState(false);
  const [expenseSaving, setExpenseSaving] = useState(false);
  const [expenseError, setExpenseError] = useState("");

  // Fetch forecast
  const forecastState = useAsync(() => {
    const params = {
      days: horizon,
      delay_days: delayDays,
    };
    if (selectedInvoiceId) {
      params.delayed_invoice_id = Number(selectedInvoiceId);
    } else if (selectedCustomerId) {
      params.delayed_customer_id = Number(selectedCustomerId);
    }
    return getCashFlowForecast(params);
  }, [horizon, delayDays, selectedCustomerId, selectedInvoiceId]);

  // Fetch expenses
  const expensesState = useAsync(listExpenses, []);

  const forecast = forecastState.data;
  const expensesList = expensesState.data ?? [];

  const handleSimulateQuick = (days) => {
    setDelayDays(days);
  };

  const handleResetSimulation = () => {
    setDelayDays(0);
    setSelectedCustomerId("");
    setSelectedInvoiceId("");
  };

  const handleCreateExpense = async (e) => {
    e.preventDefault();
    const amtErr = validateRupeeInput(expenseAmount);
    if (!expenseName.trim()) {
      setExpenseError("Please enter an expense name.");
      return;
    }
    if (amtErr) {
      setExpenseError(amtErr);
      return;
    }

    setExpenseSaving(true);
    setExpenseError("");
    try {
      await createExpense({
        name: expenseName.trim(),
        category: expenseCategory,
        amount: expenseAmount.trim(),
        expense_date: expenseDate,
        is_recurring: expenseRecurring,
        day_of_month: Number(expenseDate.split("-")[2]),
      });
      showToast("success", "Upcoming business expense added.");
      setExpenseModalOpen(false);
      setExpenseName("");
      setExpenseAmount("");
      expensesState.refresh();
      forecastState.refresh();
    } catch (err) {
      setExpenseError(err.message || "Failed to create expense.");
    } finally {
      setExpenseSaving(false);
    }
  };

  const handleDeleteExpense = async (id, name) => {
    try {
      await deleteExpense(id);
      showToast("success", `Expense "${name}" deleted.`);
      expensesState.refresh();
      forecastState.refresh();
    } catch (err) {
      showToast("error", err.message || "Failed to delete expense.");
    }
  };

  if (forecastState.loading && !forecast) {
    return <LoadingState label="Computing 30–90-day cash flow forecast…" />;
  }
  if (forecastState.error) {
    return <ErrorState message={forecastState.error.message} onRetry={forecastState.refresh} />;
  }
  if (!forecast) return null;

  const {
    starting_cash_paise,
    baseline_ending_cash_paise,
    simulated_ending_cash_paise,
    total_expected_inflows_paise,
    total_scheduled_outflows_paise,
    baseline_min_balance_paise,
    simulated_min_balance_paise,
    safety_threshold_paise,
    shortfall_detected,
    shortfall_date,
    runway_days_baseline,
    runway_days_simulated,
    affected_expenses = [],
    impact_explanation = "",
    timeline = [],
    customers_with_receivables = [],
    pending_invoices = [],
  } = forecast;

  const isSimulating = delayDays > 0;
  const netProjectedPaise = baseline_ending_cash_paise - starting_cash_paise;
  const simulationDiffPaise = simulated_ending_cash_paise - baseline_ending_cash_paise;
  const minDiffPaise = baseline_min_balance_paise - simulated_min_balance_paise;

  // Chart data
  const chartData = timeline.map((pt) => ({
    date: pt.day_label,
    fullDate: pt.date,
    baseline: Math.round(pt.balance_baseline_paise / 100),
    simulated: Math.round(pt.balance_simulated_paise / 100),
    safety: Math.round(pt.safety_threshold_paise / 100),
    inflow: Math.round(pt.inflow_baseline_paise / 100),
    outflow: Math.round(pt.outflow_paise / 100),
  }));

  const customerOptions = [
    { value: "", label: "All Customers (Global Late Payment)" },
    ...customers_with_receivables.map((c) => ({
      value: String(c.customer_id),
      label: `${c.customer_name} (Owes ${formatPaiseToRupees(c.outstanding_paise)})`,
    })),
  ];

  const invoiceOptions = [
    { value: "", label: "Or select a specific invoice…" },
    ...pending_invoices.map((inv) => ({
      value: String(inv.invoice_id),
      label: `${inv.invoice_number} — ${inv.customer_name} (${formatPaiseToRupees(inv.outstanding_paise)})`,
    })),
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <PageHeader
          title="Cash-Flow Forecasting & What-If Simulator"
          description="Projected cash balance, expected customer payments and upcoming business outflows. Projections are estimates."
        />

        <div className="flex flex-wrap items-center gap-2">
          {HORIZON_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setHorizon(opt.value)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                horizon === opt.value
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
              }`}
            >
              {opt.label}
            </button>
          ))}

          <Button variant="secondary" onClick={() => setExpenseModalOpen(true)}>
            <Plus className="h-4 w-4" />
            Add Expense
          </Button>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <SummaryItem
          label="Starting Cash"
          value={formatPaiseToRupees(starting_cash_paise)}
        />
        <SummaryItem
          label="Expected Inflows"
          value={formatPaiseToRupees(total_expected_inflows_paise)}
          tone="success"
        />
        <SummaryItem
          label="Scheduled Outflows"
          value={formatPaiseToRupees(total_scheduled_outflows_paise)}
          tone="danger"
        />
        <SummaryItem
          label="Baseline Ending Cash"
          value={formatPaiseToRupees(baseline_ending_cash_paise)}
          tone={baseline_ending_cash_paise < safety_threshold_paise ? "danger" : "default"}
        />
        <SummaryItem
          label={isSimulating ? "Simulated Ending Cash" : "Cash Runway"}
          value={
            isSimulating
              ? formatPaiseToRupees(simulated_ending_cash_paise)
              : `~${runway_days_baseline} days`
          }
          tone={shortfall_detected ? "danger" : isSimulating ? "warning" : "default"}
        />
      </div>

      {/* What-If Simulation Interactive Control Panel */}
      <div className="rounded-2xl border border-indigo-200 dark:border-indigo-500/30 bg-indigo-50/50 dark:bg-slate-900/95 p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <Sliders className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            <h3 className="font-display text-base font-bold text-slate-900 dark:text-slate-100">
              Interactive Scenario Simulator: &ldquo;What if customer payments are delayed?&rdquo;
            </h3>
          </div>
          {isSimulating && (
            <button
              type="button"
              onClick={handleResetSimulation}
              className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-700 dark:text-indigo-300 hover:text-indigo-900 dark:hover:text-indigo-200 hover:underline"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Reset Simulation to Baseline
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              1. Select Customer
            </label>
            <Select
              options={customerOptions}
              value={selectedCustomerId}
              disabled={Boolean(selectedInvoiceId)}
              onChange={(e) => {
                setSelectedCustomerId(e.target.value);
                if (delayDays === 0) setDelayDays(15);
              }}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              OR Select Specific Invoice
            </label>
            <Select
              options={invoiceOptions}
              value={selectedInvoiceId}
              onChange={(e) => {
                setSelectedInvoiceId(e.target.value);
                if (delayDays === 0) setDelayDays(15);
              }}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300 mb-1">
              2. Simulate Delay:{" "}
              <span className="text-indigo-700 dark:text-indigo-300 font-bold">{delayDays} Days</span>
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handleSimulateQuick(0)}
                className={`flex-1 rounded-lg py-1.5 text-xs font-semibold border transition-colors ${
                  delayDays === 0
                    ? "bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 border-slate-900 dark:border-slate-100"
                    : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700"
                }`}
              >
                0d (Base)
              </button>
              {[7, 15, 30].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => handleSimulateQuick(d)}
                  className={`flex-1 rounded-lg py-1.5 text-xs font-semibold border transition-colors ${
                    delayDays === d
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700"
                  }`}
                >
                  +{d} Days
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Impact Explanation & Shortfall Alert — High-Contrast Light & Dark */}
        <div className="mt-4 pt-4 border-t border-indigo-200/70 dark:border-slate-800">
          <div
            className={`rounded-xl border p-4 text-sm transition-colors ${
              shortfall_detected
                ? "bg-rose-50 dark:bg-rose-950/60 border-rose-200 dark:border-rose-500/40 text-rose-950 dark:text-rose-100"
                : isSimulating
                ? "bg-indigo-100/80 dark:bg-indigo-950/60 border-indigo-200 dark:border-indigo-500/40 text-indigo-950 dark:text-indigo-100"
                : "bg-white dark:bg-slate-800/90 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
            }`}
          >
            <div className="flex items-start gap-3">
              {shortfall_detected ? (
                <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
              ) : (
                <HelpCircle className="h-5 w-5 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-1.5 flex-1">
                <div className="font-display text-sm font-bold">
                  {shortfall_detected ? "CRITICAL CASH SHORTAGE DETECTED" : "Simulation Impact Analysis"}
                </div>
                <div className="text-xs leading-relaxed opacity-95">{impact_explanation}</div>
                {isSimulating && (
                  <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2 border-t border-current/10 text-xs">
                    <div className="rounded-lg bg-black/5 dark:bg-white/5 px-3 py-2">
                      <span className="block text-[11px] opacity-75">Baseline Ending</span>
                      <span className="font-bold tabular-nums">
                        {formatPaiseToRupees(baseline_ending_cash_paise)}
                      </span>
                    </div>
                    <div className="rounded-lg bg-black/5 dark:bg-white/5 px-3 py-2">
                      <span className="block text-[11px] opacity-75">Simulated Ending (+{delayDays}d)</span>
                      <span className="font-bold tabular-nums">
                        {formatPaiseToRupees(simulated_ending_cash_paise)}
                      </span>
                    </div>
                    <div className="rounded-lg bg-black/5 dark:bg-white/5 px-3 py-2">
                      <span className="block text-[11px] opacity-75">Impact Difference</span>
                      <span className="font-bold tabular-nums">
                        {formatPaiseToRupees(simulated_ending_cash_paise - baseline_ending_cash_paise)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Recharts Visualization */}
      <div className={CARD}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Projected Cash Trajectory ({horizon} Days)
            </h3>
            <p className="text-xs text-slate-500">
              Comparing Baseline Expected Cash Flow (Blue) vs Simulated Delay Scenario (Purple/Red)
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            <span className="flex items-center gap-1.5 text-blue-700">
              <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
              Baseline Forecast
            </span>
            {isSimulating && (
              <span className="flex items-center gap-1.5 text-purple-700">
                <span className="h-2.5 w-2.5 rounded-full bg-purple-600" />
                Simulated Scenario (+{delayDays}d)
              </span>
            )}
            <span className="flex items-center gap-1.5 text-red-600">
              <span className="h-0.5 w-3 bg-red-500" />
              Safety Reserve ({formatPaiseToRupees(safety_threshold_paise)})
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 15, right: 15, left: 10, bottom: 25 }}>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke={isDark ? "#1e293b" : "#f1f5f9"}
              />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: isDark ? "#94a3b8" : "#64748b" }} />
              <YAxis
                tick={{ fontSize: 11, fill: isDark ? "#94a3b8" : "#64748b" }}
                tickFormatter={(val) => (val >= 1000 ? `₹${val / 1000}k` : `₹${val}`)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: isDark ? "#0f172a" : "#ffffff",
                  borderColor: isDark ? "#334155" : "#e2e8f0",
                  color: isDark ? "#f1f5f9" : "#0f172a",
                  borderRadius: "12px",
                  fontSize: "12px",
                }}
                formatter={(val, name) => [
                  `₹${val.toLocaleString("en-IN")}`,
                  name === "baseline"
                    ? "Baseline Balance"
                    : name === "simulated"
                    ? `Simulated (${delayDays}d delay)`
                    : "Safety Threshold",
                ]}
              />
              <ReferenceLine
                y={Math.round(safety_threshold_paise / 100)}
                stroke="#ef4444"
                strokeDasharray="4 4"
                label={{ value: "Safety Threshold", fill: "#ef4444", fontSize: 10, position: "insideTopLeft" }}
              />
              <Line
                type="monotone"
                dataKey="baseline"
                stroke="#2563eb"
                strokeWidth={2.5}
                dot={false}
                name="baseline"
              />
              {isSimulating && (
                <Line
                  type="monotone"
                  dataKey="simulated"
                  stroke="#9333ea"
                  strokeWidth={2.5}
                  strokeDasharray="4 2"
                  dot={false}
                  name="simulated"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Two Column Layout: Affected Expenses & Scheduled Business Outflows */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scheduled Upcoming Expenses Manager */}
        <div className={CARD}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Scheduled Business Expenses</h3>
              <p className="text-xs text-slate-500">Fixed rent, payroll, software and planned operating costs</p>
            </div>
            <Button variant="secondary" onClick={() => setExpenseModalOpen(true)}>
              <Plus className="h-3.5 w-3.5" />
              Add Outflow
            </Button>
          </div>

          {expensesList.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-4">No specific expenses recorded yet.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {expensesList.map((exp) => (
                <div key={exp.id} className="py-2.5 flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-slate-900">{exp.name}</div>
                    <div className="text-xs text-slate-500 flex items-center gap-2">
                      <span className="font-semibold text-slate-600">{exp.category}</span>
                      <span>•</span>
                      <span>{exp.is_recurring ? `Monthly on day ${exp.day_of_month}` : formatDate(exp.expense_date)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-red-700">
                      -{formatPaiseToRupees(exp.amount_paise)}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDeleteExpense(exp.id, exp.name)}
                      className="text-slate-400 hover:text-red-600"
                      title="Delete expense"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Affected Expenses Under Simulation */}
        <div className={CARD}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Expenses Affected by Delayed Payments
              </h3>
              <p className="text-xs text-slate-500">
                Outflows falling during or near simulated cash reserve shortages
              </p>
            </div>
          </div>

          {!shortfall_detected || affected_expenses.length === 0 ? (
            <div className="rounded-lg bg-emerald-50/70 p-4 border border-emerald-200 text-center">
              <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-600" />
              <h4 className="mt-2 text-sm font-semibold text-emerald-900">All Expenses Protected</h4>
              <p className="mt-1 text-xs text-emerald-700">
                {isSimulating
                  ? "Even with this delay, cash on hand covers all scheduled expenses above the safety threshold."
                  : "All projected outflows are comfortably backed by current cash reserves and inflows."}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="rounded-lg bg-red-50 p-3 border border-red-200 text-xs text-red-800">
                The following scheduled payments coincide with the projected cash deficit:
              </div>
              <div className="divide-y divide-slate-100">
                {affected_expenses.map((exp, idx) => (
                  <div key={idx} className="py-2 flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-slate-900">{exp.name}</div>
                      <div className="text-xs text-slate-500">{exp.date} • {exp.category}</div>
                    </div>
                    <span className="text-sm font-bold text-red-600">
                      {formatPaiseToRupees(exp.amount_paise)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add Expense Modal */}
      {expenseModalOpen && (
        <Modal
          title="Add Upcoming Business Expense"
          open={expenseModalOpen}
          onClose={() => setExpenseModalOpen(false)}
        >
          <form onSubmit={handleCreateExpense} className="space-y-4">
            {expenseError && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200">
                {expenseError}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Expense Name <span className="text-red-500">*</span>
              </label>
              <Input
                placeholder="e.g. Server Hosting, Office Rent, Taxes"
                value={expenseName}
                onChange={(e) => setExpenseName(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
                <Select
                  options={EXPENSE_CATEGORIES}
                  value={expenseCategory}
                  onChange={(e) => setExpenseCategory(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Amount (₹) <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="25000.00"
                  value={expenseAmount}
                  onChange={(e) => setExpenseAmount(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Due Date</label>
              <Input
                type="date"
                value={expenseDate}
                onChange={(e) => setExpenseDate(e.target.value)}
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="isRecurring"
                checked={expenseRecurring}
                onChange={(e) => setExpenseRecurring(e.target.checked)}
                className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              <label htmlFor="isRecurring" className="text-sm text-slate-700">
                Repeat monthly on this day of the month
              </label>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
              <Button variant="secondary" onClick={() => setExpenseModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={expenseSaving}>
                Save Expense
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

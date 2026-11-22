import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import {
  ArrowRight,
  BarChart3,
  Bell,
  Boxes,
  CheckCircle2,
  FileText,
  Layers,
  Moon,
  ShieldCheck,
  Sparkles,
  StickyNote,
  Sun,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";

const FEATURES = [
  {
    icon: FileText,
    title: "2D Interactive Invoice Studio",
    desc: "Build GST-ready invoices with live paper preview, custom business logo, catalogue auto-fill, and one-click print/PDF.",
    color: "text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/60",
  },
  {
    icon: Boxes,
    title: "Product Catalogue & Stock Ledger",
    desc: "Manage physical products and services, track stock movements, prevent negative inventory, and auto-deduct stock on sent invoices.",
    color: "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60",
  },
  {
    icon: TrendingUp,
    title: "30/60/90-Day Cash-Flow Simulator",
    desc: "Forecast cash balance and runway from real unpaid invoices and scheduled expenses, with non-destructive What-If delay tests.",
    color: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60",
  },
  {
    icon: Sparkles,
    title: "Gemini AI Finance Copilot",
    desc: "Ask questions in plain English or voice. Grounded strictly in your live ledger via read-only tools with sensitive PII redaction.",
    color: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/60",
  },
  {
    icon: Bell,
    title: "Smart 5-Tier Payment Reminders",
    desc: "Generate polite-to-firm WhatsApp, Email, and SMS follow-up templates tailored to each overdue invoice and log every follow-up.",
    color: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/60",
  },
  {
    icon: StickyNote,
    title: "Business Notepad & Isolation",
    desc: "Capture supplier notes, daily checklists, and pinned reminders inside your own private, business-scoped workspace.",
    color: "text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-950/60",
  },
];

const SHOWCASE_TABS = [
  {
    id: "dashboard",
    label: "Financial Command",
    headline: "Your entire business health on one calm screen",
    bullets: [
      "Live receivables, overdue exposure, cash on hand, and estimated runway days",
      "Actionable alerts for overdue invoices, upcoming bills, and low-stock items",
      "Receivables ageing breakdown and invoice pipeline built from real ledger data",
    ],
    metricLabel: "Ledger Integrity",
    metricValue: "100% Integer Paise",
    badge: "Real-Time Overview",
  },
  {
    id: "invoicing",
    label: "Invoice Studio",
    headline: "Draft, brand, and send GST invoices in under a minute",
    bullets: [
      "Pick products or services directly from your catalogue with automatic pricing & GST",
      "Live branded paper preview featuring your uploaded business logo",
      "Atomic stock deduction triggers only when a draft invoice is officially sent",
    ],
    metricLabel: "Workflow",
    metricValue: "3-Step Guided Studio",
    badge: "Catalogue-Linked",
  },
  {
    id: "inventory",
    label: "Stock & Catalogue",
    headline: "Never lose track of stock or oversell an item",
    bullets: [
      "Separate physical products (stock-tracked) and services (non-stock)",
      "Complete movement ledger recording initial stock, restocks, sales, and adjustments",
      "Configurable negative-stock protection and automatic low-stock dashboard alerts",
    ],
    metricLabel: "Audit Trail",
    metricValue: "Every Unit Accounted",
    badge: "Inventory Ledger",
  },
  {
    id: "copilot",
    label: "AI Finance Copilot",
    headline: "Ask your ledger anything — by text or voice",
    bullets: [
      "Powered by Google Gemini with read-only backend financial tools",
      "Answers distinguish actual ledger metrics, forecast estimates, and what-if simulations",
      "Persistent conversation history saved per business with collapsible sidebar",
    ],
    metricLabel: "Safety",
    metricValue: "Read-Only & Redacted",
    badge: "Gemini Powered",
  },
];

export default function LandingPage() {
  const { isAuthenticated, onboardingCompleted, loading } = useAuth();
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState("dashboard");

  if (!loading && isAuthenticated) {
    return <Navigate to={onboardingCompleted ? "/dashboard" : "/onboarding"} replace />;
  }

  const currentShowcase = SHOWCASE_TABS.find((t) => t.id === activeTab) || SHOWCASE_TABS[0];
  const isDark =
    theme === "dark" ||
    (theme === "system" &&
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 transition-colors">
      {/* Navbar */}
      <header className="sticky top-0 z-40 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/85 dark:bg-slate-950/85 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm">
              <Layers className="h-5 w-5" />
            </div>
            <div className="leading-tight">
              <span className="font-display text-lg font-extrabold tracking-tight text-slate-900 dark:text-white">
                Chitragupta
              </span>
              <span className="hidden sm:block text-[10px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Smart Business Operations
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-slate-600 dark:text-slate-300">
            <a href="#features" className="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
              How It Works
            </a>
            <a href="#showcase" className="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
              Product Tour
            </a>
            <a href="#benefits" className="hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
              Why Chitragupta
            </a>
          </nav>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => setTheme(isDark ? "light" : "dark")}
              aria-label="Toggle theme"
              className="rounded-lg border border-slate-200 dark:border-slate-800 p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <Link
              to="/login"
              className="rounded-lg px-3.5 py-2 text-sm font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 transition-colors"
            >
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-20 sm:pt-24 sm:pb-28">
        <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_rgba(20,184,166,0.14),_transparent_55%)] dark:bg-[radial-gradient(ellipse_at_top,_rgba(20,184,166,0.12),_transparent_55%)]" />
        <div className="mx-auto max-w-6xl px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand-200 dark:border-brand-800/70 bg-brand-50/80 dark:bg-brand-950/50 px-3.5 py-1 text-xs font-semibold text-brand-700 dark:text-brand-300 mb-6">
            <Sparkles className="h-3.5 w-3.5" />
            Built for Solo Founders, Shopkeepers & Small Businesses
          </div>

          <h1 className="mx-auto max-w-4xl font-display text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-5xl lg:text-6xl leading-[1.1]">
            Run your billing, inventory, and cash flow from{" "}
            <span className="bg-gradient-to-r from-brand-600 to-emerald-500 dark:from-brand-400 dark:to-emerald-300 bg-clip-text text-transparent">
              one intelligent back office
            </span>
            .
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
            Chitragupta brings GST invoicing, product &amp; stock tracking, 90-day cash-flow
            forecasting, payment reminders, business notes, and a Gemini AI Finance Copilot into one
            clean workspace tailored to your business.
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3.5">
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3.5 text-sm font-semibold text-white shadow-md shadow-brand-600/20 hover:bg-brand-700 transition-all"
            >
              Create Your Business Workspace
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-6 py-3.5 text-sm font-semibold text-slate-800 dark:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
            >
              Sign In to Existing Account
            </Link>
          </div>

          {/* Interactive Architecture Strip */}
          <div className="mt-14 mx-auto max-w-5xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 sm:p-7 shadow-xl shadow-slate-900/5 dark:shadow-black/30 text-left">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Your Private Workspace Preview
                </span>
              </div>
              <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-3 py-1 text-xs font-medium text-slate-600 dark:text-slate-300">
                Starts 100% clean — zero dummy clutter
              </span>
            </div>
            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: "Invoicing & GST", value: "Draft → Send → Paid", icon: FileText },
                { label: "Inventory Sync", value: "Auto-Deduct on Send", icon: Boxes },
                { label: "Cash Forecast", value: "30 / 60 / 90 Days", icon: BarChart3 },
                { label: "AI Copilot", value: "Read-Only Ledger Q&A", icon: Sparkles },
              ].map((card) => (
                <div
                  key={card.label}
                  className="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/60 p-4"
                >
                  <card.icon className="h-5 w-5 text-brand-600 dark:text-brand-400 mb-2.5" />
                  <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{card.label}</p>
                  <p className="mt-1 font-display text-sm font-bold text-slate-900 dark:text-white">
                    {card.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 border-t border-slate-200/70 dark:border-slate-800/70 bg-white dark:bg-slate-900/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              Everything You Need
            </p>
            <h2 className="mt-2 font-display text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
              Operational clarity without spreadsheet chaos
            </h2>
            <p className="mt-3 text-slate-600 dark:text-slate-300">
              Every module shares one exact integer-paise financial engine so your invoices, payments,
              stock counts, and cash forecasts never drift out of sync.
            </p>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm hover:border-brand-300 dark:hover:border-brand-700 transition-colors"
              >
                <div className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${f.color}`}>
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-display text-lg font-bold text-slate-900 dark:text-white">
                  {f.title}
                </h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 border-t border-slate-200/70 dark:border-slate-800/70">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="text-center max-w-2xl mx-auto">
            <p className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              Simple Onboarding
            </p>
            <h2 className="mt-2 font-display text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
              From signup to your first branded invoice in minutes
            </h2>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
            {[
              {
                step: "01",
                title: "Create Your Account",
                desc: "Sign up with your email and password. Your account is secured with scrypt hashing and HttpOnly session cookies.",
              },
              {
                step: "02",
                title: "Brand Your Business Profile",
                desc: "Add your business name, category, logo, GSTIN, and payment details during guided onboarding.",
              },
              {
                step: "03",
                title: "Bill, Track Stock & Forecast",
                desc: "Add customers and catalogue items, issue invoices, record payments, and ask the AI Copilot for instant financial answers.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6"
              >
                <span className="font-display text-3xl font-extrabold text-brand-600/30 dark:text-brand-400/30">
                  {item.step}
                </span>
                <h3 className="mt-3 font-display text-lg font-bold text-slate-900 dark:text-white">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Interactive Product Showcase */}
      <section id="showcase" className="py-20 border-t border-slate-200/70 dark:border-slate-800/70 bg-white dark:bg-slate-900/40">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                Interactive Product Tour
              </p>
              <h2 className="mt-2 font-display text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
                Explore the modules inside Chitragupta
              </h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {SHOWCASE_TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition-all ${
                    activeTab === tab.id
                      ? "bg-brand-600 text-white shadow-sm"
                      : "border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-12 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-6 sm:p-8">
            <div className="lg:col-span-7 flex flex-col justify-center">
              <span className="inline-flex w-fit items-center rounded-full bg-brand-100 dark:bg-brand-950/80 px-3 py-1 text-xs font-semibold text-brand-700 dark:text-brand-300">
                {currentShowcase.badge}
              </span>
              <h3 className="mt-4 font-display text-2xl font-extrabold text-slate-900 dark:text-white">
                {currentShowcase.headline}
              </h3>
              <ul className="mt-5 space-y-3">
                {currentShowcase.bullets.map((b) => (
                  <li key={b} className="flex items-start gap-2.5 text-sm text-slate-700 dark:text-slate-300">
                    <CheckCircle2 className="h-4.5 w-4.5 shrink-0 text-brand-600 dark:text-brand-400 mt-0.5" />
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="lg:col-span-5 flex flex-col justify-between rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  {currentShowcase.metricLabel}
                </p>
                <p className="mt-2 font-display text-2xl font-extrabold text-brand-600 dark:text-brand-400">
                  {currentShowcase.metricValue}
                </p>
              </div>
              <div className="mt-6 space-y-2.5 border-t border-slate-100 dark:border-slate-800 pt-5 text-xs text-slate-600 dark:text-slate-400">
                <div className="flex items-center justify-between">
                  <span>Multi-business isolation</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">Enforced</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Light &amp; Dark Theme</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">Included</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Clean account onboarding</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">Default</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section id="benefits" className="py-20 border-t border-slate-200/70 dark:border-slate-800/70">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 grid grid-cols-1 gap-8 md:grid-cols-3">
          {[
            {
              icon: ShieldCheck,
              title: "Built for Financial Accuracy",
              desc: "All rupee math uses integer paise with exact half-up GST rounding, overpayment protection, and full payment reversal audit trails.",
            },
            {
              icon: Wallet,
              title: "Designed for Solo Operators",
              desc: "No bloated enterprise menus. Just fast workflows for customers, catalogue, invoices, stock, cash flow, and daily business notes.",
            },
            {
              icon: Sparkles,
              title: "Transparent AI Assistance",
              desc: "Your AI Finance Copilot reads only your business's live data via strict read-only tools and never modifies financial records on its own.",
            },
          ].map((b) => (
            <div key={b.title} className="flex flex-col gap-3">
              <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-100 dark:bg-brand-950/70 text-brand-700 dark:text-brand-300">
                <b.icon className="h-5 w-5" />
              </div>
              <h3 className="font-display text-lg font-bold text-slate-900 dark:text-white">{b.title}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{b.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <div className="rounded-3xl bg-gradient-to-br from-brand-700 via-brand-600 to-emerald-600 px-6 py-12 sm:px-12 text-center text-white shadow-xl">
            <h2 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
              Ready to organize your entire business?
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-sm sm:text-base text-brand-50">
              Create your private Chitragupta workspace, upload your business logo, and start
              managing invoices, inventory, and cash flow today.
            </p>
            <div className="mt-7 flex flex-wrap justify-center gap-3">
              <Link
                to="/signup"
                className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-bold text-brand-700 shadow-sm hover:bg-brand-50 transition-colors"
              >
                Create Free Workspace
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 rounded-xl border border-white/30 bg-white/10 px-6 py-3 text-sm font-semibold text-white hover:bg-white/20 transition-colors"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-8 text-center text-xs text-slate-500 dark:text-slate-400">
        <div className="mx-auto max-w-6xl px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p className="font-semibold text-slate-700 dark:text-slate-300">
            Chitragupta — Smart Business Operations Platform
          </p>
          <p>Invoices · Catalogue &amp; Inventory · Cash Flow · Reminders · AI Finance Copilot</p>
        </div>
      </footer>
    </div>
  );
}

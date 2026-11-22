import { useEffect, useRef, useState } from "react";
import { Check, CheckCircle2, ImagePlus, RefreshCw, Save, Settings, Trash2 } from "lucide-react";
import Button from "../components/common/Button.jsx";
import ConfirmDialog from "../components/common/ConfirmDialog.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import Input from "../components/common/Input.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import Select from "../components/common/Select.jsx";
import Textarea from "../components/common/Textarea.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { getSettings, updateSettings } from "../services/settingsService.js";
import { deleteBusinessLogo, uploadBusinessLogo } from "../services/uploadService.js";
import { resetAndSeedDemo } from "../services/demoService.js";
import { paiseToRupeeInput, rupeeStringToPaise, validateRupeeInput } from "../utils/money.js";

const CARD = "rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#111827] shadow-sm p-6";

export default function SettingsPage() {
  const showToast = useToast();
  const { refreshAuth } = useAuth();
  const { data: initialSettings, loading, error, refresh } = useAsync(getSettings, []);

  const [form, setForm] = useState({
    business_name: "",
    owner_name: "",
    category: "Services & Consulting",
    description: "",
    allow_negative_stock: false,
    email: "",
    phone: "",
    address: "",
    gstin: "",
    upi_id: "",
    bank_name: "",
    bank_account: "",
    bank_ifsc: "",
    default_payment_terms_days: "15",
    default_tax_percent: "18",
    initial_cash_balance: "250000.00",
    monthly_recurring_expenses: "65000.00",
    safety_cash_threshold: "50000.00",
  });

  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [localLogoPreview, setLocalLogoPreview] = useState(null);
  const logoInputRef = useRef(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [reseedConfirmOpen, setReseedConfirmOpen] = useState(false);
  const [reseeding, setReseeding] = useState(false);

  useEffect(() => {
    if (initialSettings) {
      setForm({
        business_name: initialSettings.business_name ?? "",
        owner_name: initialSettings.owner_name ?? "",
        category: initialSettings.category ?? "Services & Consulting",
        description: initialSettings.description ?? "",
        allow_negative_stock: Boolean(initialSettings.allow_negative_stock),
        email: initialSettings.email ?? "",
        phone: initialSettings.phone ?? "",
        address: initialSettings.address ?? "",
        gstin: initialSettings.gstin ?? "",
        upi_id: initialSettings.upi_id ?? "",
        bank_name: initialSettings.bank_name ?? "",
        bank_account: initialSettings.bank_account ?? "",
        bank_ifsc: initialSettings.bank_ifsc ?? "",
        default_payment_terms_days: String(initialSettings.default_payment_terms_days ?? 15),
        default_tax_percent: String(initialSettings.default_tax_percent ?? 18),
        initial_cash_balance: paiseToRupeeInput(initialSettings.initial_cash_balance_paise),
        monthly_recurring_expenses: paiseToRupeeInput(initialSettings.monthly_recurring_expenses_paise),
        safety_cash_threshold: paiseToRupeeInput(initialSettings.safety_cash_threshold_paise),
      });
    }
  }, [initialSettings]);

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      showToast("error", "Logo must be 5 MB or smaller.");
      return;
    }
    setLocalLogoPreview(URL.createObjectURL(file));
    setUploadingLogo(true);
    try {
      await uploadBusinessLogo(file);
      showToast("success", "Business logo uploaded successfully.");
      await refresh();
      await refreshAuth();
      setLocalLogoPreview(null);
    } catch (err) {
      setLocalLogoPreview(null);
      showToast("error", err.message || "Could not upload logo. Use PNG, JPEG, or WebP.");
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleLogoRemove = async () => {
    setUploadingLogo(true);
    try {
      await deleteBusinessLogo();
      showToast("success", "Business logo removed.");
      refresh();
      refreshAuth();
    } catch (err) {
      showToast("error", err.message || "Could not remove logo.");
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setSaveSuccess(false);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);

    try {
      await updateSettings({
        business_name: form.business_name.trim(),
        owner_name: form.owner_name.trim(),
        category: form.category.trim() || null,
        description: form.description.trim() || null,
        allow_negative_stock: Boolean(form.allow_negative_stock),
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        address: form.address.trim() || null,
        gstin: form.gstin.trim() || null,
        upi_id: form.upi_id.trim() || null,
        bank_name: form.bank_name.trim() || null,
        bank_account: form.bank_account.trim() || null,
        bank_ifsc: form.bank_ifsc.trim() || null,
        default_payment_terms_days: Number(form.default_payment_terms_days),
        default_tax_percent: Number(form.default_tax_percent),
        initial_cash_balance: form.initial_cash_balance.trim(),
        monthly_recurring_expenses: form.monthly_recurring_expenses.trim(),
        safety_cash_threshold: form.safety_cash_threshold.trim(),
      });
      setSaveSuccess(true);
      showToast("success", "Settings saved successfully.");
      refresh();
      refreshAuth();
    } catch (err) {
      showToast("error", err.message || "Failed to save settings.");
    } finally {
      setSaving(false);
    }
  };

  const handleReseed = async () => {
    setReseeding(true);
    try {
      await resetAndSeedDemo();
      showToast("success", "Demonstration data re-seeded successfully!");
      setReseedConfirmOpen(false);
      refresh();
    } catch (err) {
      showToast("error", err.message || "Failed to re-seed demo data.");
    } finally {
      setReseeding(false);
    }
  };

  if (loading && !initialSettings) return <LoadingState label="Loading settings…" />;
  if (error) return <ErrorState message={error.message} onRetry={refresh} />;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Business Profile & Settings"
        description="Configure your one-person back office profile, bank details, cash reserves and invoice defaults."
      />

      <form onSubmit={handleSave} className="space-y-6">
        {/* Business Profile */}
        <div className={CARD}>
          <h2 className="font-display text-base font-bold text-slate-900 dark:text-slate-100 border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
            Business Branding &amp; Profile
          </h2>

          {/* Business Logo Uploader */}
          <div className="mb-5 flex flex-wrap items-center gap-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-900/50 p-4">
            {localLogoPreview || initialSettings?.logo_url ? (
              <img
                src={localLogoPreview || initialSettings.logo_url}
                alt="Business logo"
                className="h-14 w-14 rounded-xl object-cover border border-slate-200 dark:border-slate-700 bg-white"
              />
            ) : (
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-slate-200/80 dark:bg-slate-800 text-slate-500">
                <ImagePlus className="h-6 w-6" />
              </div>
            )}
            <div className="flex-1 min-w-[200px]">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Business Logo
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Appears in the sidebar, dashboard, and invoices. PNG, JPEG, or WebP (max 5 MB).
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                ref={logoInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,.png,.jpg,.jpeg,.webp"
                disabled={uploadingLogo}
                onChange={handleLogoUpload}
                className="sr-only"
              />
              <button
                type="button"
                disabled={uploadingLogo}
                onClick={() => logoInputRef.current?.click()}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-60"
              >
                <ImagePlus className="h-3.5 w-3.5" />
                {uploadingLogo
                  ? "Uploading…"
                  : initialSettings?.logo_url
                  ? "Replace Logo"
                  : "Upload Logo"}
              </button>
              {initialSettings?.logo_url && (
                <button
                  type="button"
                  disabled={uploadingLogo}
                  onClick={handleLogoRemove}
                  className="inline-flex items-center gap-1 rounded-xl border border-rose-200 dark:border-rose-800 px-3 py-2 text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Remove
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Business Name <span className="text-red-500">*</span>
              </label>
              <Input
                value={form.business_name}
                onChange={handleChange("business_name")}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Owner / Consultant Name <span className="text-red-500">*</span>
              </label>
              <Input
                value={form.owner_name}
                onChange={handleChange("owner_name")}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Business Category
              </label>
              <Input
                value={form.category}
                onChange={handleChange("category")}
                placeholder="e.g. Retail & Trading, Consulting"
              />
            </div>
            <div className="flex items-center pt-5">
              <label className="flex items-center gap-2.5 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.allow_negative_stock}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, allow_negative_stock: e.target.checked }))
                  }
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                <span>Allow negative stock on sent invoices</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Official Email</label>
              <Input
                type="email"
                value={form.email}
                onChange={handleChange("email")}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number</label>
              <Input
                value={form.phone}
                onChange={handleChange("phone")}
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Business Address</label>
              <Textarea
                rows={2}
                value={form.address}
                onChange={handleChange("address")}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">GSTIN / Tax ID</label>
              <Input
                placeholder="29AAAAA0000A1Z5"
                value={form.gstin}
                onChange={handleChange("gstin")}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Currency</label>
              <input
                type="text"
                disabled
                value="INR (₹) — Indian Rupee"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
              />
            </div>
          </div>
        </div>

        {/* Payment & Banking Details */}
        <div className={CARD}>
          <h2 className="text-base font-semibold text-slate-900 border-b border-slate-200 pb-3 mb-4">
            Payment & Banking Details
          </h2>
          <p className="text-xs text-slate-500 -mt-2 mb-4">
            These payment coordinates are automatically attached to invoices and assisted WhatsApp/Email payment reminders.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Primary UPI ID</label>
              <Input
                placeholder="aditi@okhdfcbank"
                value={form.upi_id}
                onChange={handleChange("upi_id")}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Bank Name</label>
              <Input
                placeholder="HDFC Bank"
                value={form.bank_name}
                onChange={handleChange("bank_name")}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Account Number</label>
              <Input
                placeholder="50100456789012"
                value={form.bank_account}
                onChange={handleChange("bank_account")}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">IFSC Code</label>
              <Input
                placeholder="HDFC0001234"
                value={form.bank_ifsc}
                onChange={handleChange("bank_ifsc")}
              />
            </div>
          </div>
        </div>

        {/* Financial Runway & Cash Flow Baseline */}
        <div className={CARD}>
          <h2 className="text-base font-semibold text-slate-900 border-b border-slate-200 pb-3 mb-4">
            Cash Flow & Forecasting Parameters
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Starting Cash Balance (₹)
              </label>
              <Input
                value={form.initial_cash_balance}
                onChange={handleChange("initial_cash_balance")}
              />
              <span className="text-[11px] text-slate-500">Baseline cash at bank</span>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Estimated Monthly Outflows (₹)
              </label>
              <Input
                value={form.monthly_recurring_expenses}
                onChange={handleChange("monthly_recurring_expenses")}
              />
              <span className="text-[11px] text-slate-500">Fixed monthly burn (rent, tools, staff)</span>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Safety Reserve Threshold (₹)
              </label>
              <Input
                value={form.safety_cash_threshold}
                onChange={handleChange("safety_cash_threshold")}
              />
              <span className="text-[11px] text-slate-500">Triggers shortage alerts when balance dips</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-100">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Default Payment Terms (Days)
              </label>
              <Input
                type="number"
                min="0"
                max="180"
                value={form.default_payment_terms_days}
                onChange={handleChange("default_payment_terms_days")}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Default GST Tax (%)
              </label>
              <Input
                type="number"
                min="0"
                max="100"
                value={form.default_tax_percent}
                onChange={handleChange("default_tax_percent")}
              />
            </div>
          </div>
        </div>

        {/* Submit Actions */}
        <div className="flex items-center justify-between pt-2">
          <Button type="submit" loading={saving} className="bg-brand-600 hover:bg-brand-700">
            {saveSuccess ? (
              <>
                <Check className="h-4 w-4" />
                Settings Saved
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save Settings
              </>
            )}
          </Button>

          <Button
            type="button"
            variant="secondary"
            onClick={() => setReseedConfirmOpen(true)}
            className="text-slate-600 hover:text-slate-900 border-dashed"
          >
            <RefreshCw className="h-4 w-4" />
            Reset & Re-seed Demo Data
          </Button>
        </div>
      </form>

      {/* Re-seed confirmation dialog */}
      <ConfirmDialog
        open={reseedConfirmOpen}
        title="Reset & Re-seed Demo Data?"
        message="This will repopulate the database with synthetic micro-business demonstration records (customers, invoices, payments, audit history, and expenses). Ideal for hackathon evaluation."
        confirmLabel="Reset to Demo State"
        variant="danger"
        loading={reseeding}
        onConfirm={handleReseed}
        onCancel={() => setReseedConfirmOpen(false)}
      />
    </div>
  );
}

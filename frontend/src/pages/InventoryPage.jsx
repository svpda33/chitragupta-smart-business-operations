import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  Boxes,
  Loader2,
  PackageCheck,
  PackageX,
  Plus,
  RefreshCw,
  SlidersHorizontal,
  X,
} from "lucide-react";
import {
  adjustProductStock,
  getInventorySummary,
  listProducts,
} from "../services/productService.js";
import { formatDate } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";
import { useToast } from "../context/ToastContext.jsx";

export default function InventoryPage() {
  const showToast = useToast();
  const addToast = useCallback((msg, type = "info") => showToast(type, msg), [showToast]);
  const [summary, setSummary] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Stock adjustment modal
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [movementType, setMovementType] = useState("restock");
  const [quantity, setQuantity] = useState("10");
  const [reason, setReason] = useState("");
  const [reference, setReference] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [sumData, prodData] = await Promise.all([
        getInventorySummary(),
        listProducts({ item_type: "product" }),
      ]);
      setSummary(sumData);
      setProducts(Array.isArray(prodData) ? prodData : []);
    } catch (err) {
      addToast(err.message || "Failed to load inventory.", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function openAdjustModal(productId = "", defaultType = "restock") {
    setSelectedProductId(productId ? String(productId) : products[0] ? String(products[0].id) : "");
    setMovementType(defaultType);
    setQuantity(defaultType === "restock" ? "10" : "-1");
    setReason(defaultType === "restock" ? "Supplier restock" : "Manual stock count adjustment");
    setReference("");
    setModalError("");
    setModalOpen(true);
  }

  async function handleAdjustSubmit(e) {
    e.preventDefault();
    setModalError("");
    if (!selectedProductId) {
      setModalError("Please select a product.");
      return;
    }
    const qtyNum = Number(quantity);
    if (!Number.isInteger(qtyNum) || qtyNum === 0) {
      setModalError("Quantity change must be a non-zero whole number.");
      return;
    }
    setSubmitting(true);
    try {
      await adjustProductStock(Number(selectedProductId), {
        movement_type: movementType,
        quantity_change: qtyNum,
        reason: reason.trim() || "Stock update",
        reference: reference.trim() || null,
      });
      addToast("Stock movement recorded.", "success");
      setModalOpen(false);
      loadData();
    } catch (err) {
      setModalError(err.message || "Could not adjust stock.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold text-slate-900 dark:text-white">
            Inventory &amp; Stock Ledger
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Track real-time stock quantities, restock alerts, and automatic invoice deductions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/catalogue"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            Manage Catalogue
          </Link>
          <button
            type="button"
            disabled={products.length === 0}
            onClick={() => openAdjustModal("", "restock")}
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Record Stock Movement
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Active Products
            </span>
            <Boxes className="h-4 w-4 text-brand-600 dark:text-brand-400" />
          </div>
          <p className="mt-2 font-display text-2xl font-extrabold text-slate-900 dark:text-white">
            {summary?.total_active_products ?? 0}
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {summary?.total_stock_units ?? 0} total units on hand
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Low Stock Alerts
            </span>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <p className="mt-2 font-display text-2xl font-extrabold text-amber-600 dark:text-amber-400">
            {summary?.low_stock_count ?? 0}
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            At or below reorder threshold
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Out of Stock
            </span>
            <PackageX className="h-4 w-4 text-rose-500" />
          </div>
          <p className="mt-2 font-display text-2xl font-extrabold text-rose-600 dark:text-rose-400">
            {summary?.out_of_stock_count ?? 0}
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Needs immediate restocking
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Stock Valuation
            </span>
            <PackageCheck className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="mt-2 font-display text-2xl font-extrabold text-slate-900 dark:text-white">
            {formatPaiseToRupees(summary?.inventory_valuation_paise ?? 0)}
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Across {summary?.valued_products_count ?? 0} priced items
          </p>
        </div>
      </div>

      {/* Low Stock Attention Section */}
      {summary?.low_stock_items?.length > 0 && (
        <div className="rounded-2xl border border-amber-200 dark:border-amber-800/80 bg-amber-50/70 dark:bg-amber-950/30 p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-4.5 w-4.5 text-amber-600 dark:text-amber-400" />
            <h2 className="font-display text-sm font-bold text-amber-900 dark:text-amber-200">
              Items Needing Restock ({summary.low_stock_items.length})
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {summary.low_stock_items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-amber-200/80 dark:border-amber-800/60 bg-white dark:bg-slate-900 p-3.5"
              >
                <div className="min-w-0">
                  <p className="text-sm font-bold text-slate-900 dark:text-white truncate">
                    {item.name}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {item.stock_quantity} {item.unit} left (min {item.min_stock_threshold})
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => openAdjustModal(item.id, "restock")}
                  className="shrink-0 inline-flex items-center gap-1 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Restock
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stock Movement Ledger */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
          <h2 className="font-display text-base font-bold text-slate-900 dark:text-white">
            Recent Stock Movements
          </h2>
          <button
            type="button"
            onClick={loadData}
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-brand-600"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>

        {!summary?.recent_movements?.length ? (
          <div className="p-10 text-center text-sm text-slate-500 dark:text-slate-400">
            No stock movements recorded yet. Add physical products in the Catalogue or send an
            invoice to see automatic stock history here.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 dark:divide-slate-800 text-sm">
              <thead className="bg-slate-50 dark:bg-slate-950/60 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-5 py-3 text-left">Product</th>
                  <th className="px-5 py-3 text-left">Type</th>
                  <th className="px-5 py-3 text-right">Change</th>
                  <th className="px-5 py-3 text-right">Balance After</th>
                  <th className="px-5 py-3 text-left">Reason / Reference</th>
                  <th className="px-5 py-3 text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {summary.recent_movements.map((m) => {
                  const isPos = m.quantity_change > 0;
                  return (
                    <tr key={m.id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40">
                      <td className="px-5 py-3.5 font-semibold text-slate-900 dark:text-white">
                        {m.product_name}
                        {m.sku && (
                          <span className="ml-2 text-xs font-normal text-slate-400">{m.sku}</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 text-xs font-semibold capitalize text-slate-700 dark:text-slate-300">
                          {isPos ? (
                            <ArrowDownLeft className="h-3 w-3 text-emerald-500" />
                          ) : (
                            <ArrowUpRight className="h-3 w-3 text-rose-500" />
                          )}
                          {m.movement_type.replace("_", " ")}
                        </span>
                      </td>
                      <td
                        className={`px-5 py-3.5 text-right font-bold tabular-nums ${
                          isPos
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {isPos ? `+${m.quantity_change}` : m.quantity_change}
                      </td>
                      <td className="px-5 py-3.5 text-right font-semibold tabular-nums text-slate-900 dark:text-white">
                        {m.balance_after}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-600 dark:text-slate-300">
                        {m.reason || "—"}
                        {m.reference && (
                          <span className="ml-1.5 text-slate-400">({m.reference})</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-right text-xs text-slate-500 dark:text-slate-400">
                        {formatDate(m.created_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Adjust Stock Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">
                Record Stock Movement
              </h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {modalError && (
              <div className="mt-4 rounded-xl border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/50 p-3 text-xs text-rose-700 dark:text-rose-300">
                {modalError}
              </div>
            )}

            <form onSubmit={handleAdjustSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Product *
                </label>
                <select
                  required
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} (Current: {p.stock_quantity} {p.unit})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Movement Type
                  </label>
                  <select
                    value={movementType}
                    onChange={(e) => setMovementType(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  >
                    <option value="restock">Restock (+)</option>
                    <option value="adjustment">Adjustment (+/-)</option>
                    <option value="return_reversal">Customer Return (+)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Quantity Change *
                  </label>
                  <input
                    type="number"
                    required
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder="+10 or -2"
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Reason *
                </label>
                <input
                  type="text"
                  required
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Monthly supplier delivery"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Reference (Optional)
                </label>
                <input
                  type="text"
                  value={reference}
                  onChange={(e) => setReference(e.target.value)}
                  placeholder="PO-2026-014"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-xl border border-slate-200 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-5 py-2 text-xs font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
                >
                  {submitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  Save Movement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Archive,
  Box,
  Briefcase,
  ImagePlus,
  Loader2,
  Package,
  Pencil,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import {
  createProduct,
  deleteProduct,
  listProducts,
  updateProduct,
} from "../services/productService.js";
import { deleteProductImage, uploadProductImage } from "../services/uploadService.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";
import { useToast } from "../context/ToastContext.jsx";

const STOCK_BADGE = {
  in_stock: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800/80",
  low_stock: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800/80",
  out_of_stock: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800/80",
  service: "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/60 dark:text-indigo-300 dark:border-indigo-800/80",
};

const STOCK_LABEL = {
  in_stock: "In Stock",
  low_stock: "Low Stock",
  out_of_stock: "Out of Stock",
  service: "Service",
};

const EMPTY_FORM = {
  item_type: "product",
  name: "",
  description: "",
  sku: "",
  category: "General",
  selling_price: "",
  cost_price: "",
  tax_percent: 18,
  unit: "pcs",
  stock_quantity: 0,
  min_stock_threshold: 5,
  is_active: true,
};

export default function CataloguePage() {
  const showToast = useToast();
  const addToast = useCallback((msg, type = "info") => showToast(type, msg), [showToast]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [stockFilter, setStockFilter] = useState("all");

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const productImageInputRef = useRef(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const fetchCatalogue = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (typeFilter !== "all") params.item_type = typeFilter;
      if (stockFilter !== "all") params.stock_status = stockFilter;
      const data = await listProducts(params);
      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      addToast(err.message || "Failed to load catalogue.", "error");
    } finally {
      setLoading(false);
    }
  }, [search, typeFilter, stockFilter, addToast]);

  useEffect(() => {
    const t = setTimeout(fetchCatalogue, 200);
    return () => clearTimeout(t);
  }, [fetchCatalogue]);

  function openCreate(defaultType = "product") {
    setEditing(null);
    setForm({
      ...EMPTY_FORM,
      item_type: defaultType,
      unit: defaultType === "service" ? "hrs" : "pcs",
    });
    setImageFile(null);
    setImagePreview(null);
    setFormError("");
    setModalOpen(true);
  }

  function openEdit(item) {
    setEditing(item);
    setForm({
      item_type: item.item_type,
      name: item.name,
      description: item.description || "",
      sku: item.sku || "",
      category: item.category || "General",
      selling_price: (item.selling_price_paise / 100).toFixed(2),
      cost_price: item.cost_price_paise != null ? (item.cost_price_paise / 100).toFixed(2) : "",
      tax_percent: item.tax_percent,
      unit: item.unit || "pcs",
      stock_quantity: item.stock_quantity,
      min_stock_threshold: item.min_stock_threshold,
      is_active: item.is_active,
    });
    setImageFile(null);
    setImagePreview(item.image_url || null);
    setFormError("");
    setModalOpen(true);
  }

  function handleImagePick(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setFormError("Image must be 5 MB or smaller.");
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  }

  async function handleSave(e) {
    e.preventDefault();
    setFormError("");
    setSaving(true);
    try {
      const payload = {
        ...form,
        tax_percent: Number(form.tax_percent) || 0,
        stock_quantity: form.item_type === "product" ? Number(form.stock_quantity) || 0 : 0,
        min_stock_threshold:
          form.item_type === "product" ? Number(form.min_stock_threshold) || 0 : 0,
        cost_price: form.cost_price === "" ? null : form.cost_price,
      };
      let saved;
      if (editing) {
        saved = await updateProduct(editing.id, payload);
      } else {
        saved = await createProduct(payload);
      }

      if (imageFile && saved?.id) {
        await uploadProductImage(saved.id, imageFile);
      }

      addToast(editing ? "Catalogue item updated." : "Added to catalogue.", "success");
      setModalOpen(false);
      fetchCatalogue();
    } catch (err) {
      setFormError(err.message || "Could not save item.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRemovePhoto() {
    if (!editing) {
      setImageFile(null);
      setImagePreview(null);
      return;
    }
    try {
      await deleteProductImage(editing.id);
      setImageFile(null);
      setImagePreview(null);
      addToast("Product photo removed.", "success");
      fetchCatalogue();
    } catch (err) {
      addToast(err.message || "Could not remove photo.", "error");
    }
  }

  async function handleDelete(item) {
    if (!window.confirm(`Delete "${item.name}" from your catalogue?`)) return;
    try {
      await deleteProduct(item.id);
      addToast("Item removed from catalogue.", "success");
      fetchCatalogue();
    } catch (err) {
      addToast(err.message || "Could not delete item.", "error");
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold text-slate-900 dark:text-white">
            Products &amp; Services Catalogue
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage physical inventory items and non-stock services. Pick any item directly in the
            Invoice Studio.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => openCreate("service")}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            <Briefcase className="h-4 w-4 text-indigo-500" />
            Add Service
          </button>
          <button
            type="button"
            onClick={() => openCreate("product")}
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" />
            Add Product
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-3 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, SKU, or category..."
            className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 pl-9 pr-3 py-2 text-sm text-slate-900 dark:text-slate-100"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {["all", "product", "service"].map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTypeFilter(t)}
              className={`rounded-xl px-3.5 py-2 text-xs font-semibold capitalize transition-colors ${
                typeFilter === t
                  ? "bg-brand-600 text-white"
                  : "border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              {t === "all" ? "All Types" : `${t}s`}
            </button>
          ))}
          <select
            value={stockFilter}
            onChange={(e) => setStockFilter(e.target.value)}
            className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200"
          >
            <option value="all">All Stock Status</option>
            <option value="in_stock">In Stock</option>
            <option value="low_stock">Low Stock</option>
            <option value="out_of_stock">Out of Stock</option>
          </select>
        </div>
      </div>

      {/* Catalogue Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-12 text-center">
          <Package className="mx-auto h-10 w-10 text-slate-400" />
          <h3 className="mt-3 font-display text-lg font-bold text-slate-900 dark:text-white">
            Your catalogue is empty
          </h3>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Add your products or services once to auto-fill invoices and track inventory levels.
          </p>
          <button
            type="button"
            onClick={() => openCreate("product")}
            className="mt-5 inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-brand-700"
          >
            <Plus className="h-4 w-4" />
            Add First Product
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm hover:border-brand-300 dark:hover:border-brand-700 transition-colors"
            >
              <div>
                <div className="flex items-start gap-3.5">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={item.name}
                      className="h-14 w-14 rounded-xl object-cover border border-slate-200 dark:border-slate-700 shrink-0"
                    />
                  ) : (
                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                      {item.item_type === "service" ? (
                        <Briefcase className="h-6 w-6" />
                      ) : (
                        <Box className="h-6 w-6" />
                      )}
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold ${
                          STOCK_BADGE[item.stock_status] || STOCK_BADGE.in_stock
                        }`}
                      >
                        {STOCK_LABEL[item.stock_status] || item.stock_status}
                      </span>
                      {!item.is_active && (
                        <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                          <Archive className="h-3 w-3" /> Archived
                        </span>
                      )}
                    </div>
                    <h3 className="mt-1.5 font-display text-base font-bold text-slate-900 dark:text-white truncate">
                      {item.name}
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                      {item.category || "General"}
                      {item.sku ? ` · SKU: ${item.sku}` : ""}
                    </p>
                  </div>
                </div>

                {item.description && (
                  <p className="mt-3 text-xs text-slate-600 dark:text-slate-300 line-clamp-2">
                    {item.description}
                  </p>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-end justify-between">
                <div>
                  <p className="font-display text-lg font-extrabold text-slate-900 dark:text-white">
                    {formatPaiseToRupees(item.selling_price_paise)}
                    <span className="text-xs font-medium text-slate-400"> / {item.unit}</span>
                  </p>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    GST {item.tax_percent}%
                    {item.item_type === "product"
                      ? ` · Stock: ${item.stock_quantity} ${item.unit}`
                      : " · Non-stock service"}
                  </p>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => openEdit(item)}
                    className="rounded-lg border border-slate-200 dark:border-slate-700 p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                    title="Edit"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(item)}
                    className="rounded-lg border border-slate-200 dark:border-slate-700 p-2 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50"
                    title="Delete"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm overflow-y-auto">
          <div className="my-8 w-full max-w-xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
              <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">
                {editing ? `Edit ${editing.name}` : "Add Catalogue Item"}
              </h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {formError && (
              <div className="mt-4 rounded-xl border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/50 p-3 text-xs text-rose-700 dark:text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleSave} className="mt-4 space-y-4">
              {/* Type Selector */}
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "product", label: "Physical Product (Stock Tracked)", icon: Box },
                  { id: "service", label: "Service (No Stock Tracking)", icon: Briefcase },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() =>
                      setForm((f) => ({
                        ...f,
                        item_type: opt.id,
                        unit: opt.id === "service" && f.unit === "pcs" ? "hrs" : f.unit,
                      }))
                    }
                    className={`flex items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-xs font-semibold transition-colors ${
                      form.item_type === opt.id
                        ? "border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300"
                        : "border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300"
                    }`}
                  >
                    <opt.icon className="h-4 w-4" />
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* Photo Upload */}
              <div className="flex items-center gap-3 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 p-3">
                {imagePreview ? (
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="h-12 w-12 rounded-lg object-cover border border-slate-200 dark:border-slate-700"
                  />
                ) : (
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-400">
                    <ImagePlus className="h-5 w-5" />
                  </div>
                )}
                <div className="flex-1 text-xs text-slate-500 dark:text-slate-400">
                  Optional photo (PNG/JPEG/WebP, max 2 MB)
                </div>
                <input
                  ref={productImageInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp,.png,.jpg,.jpeg,.webp"
                  onChange={handleImagePick}
                  className="sr-only"
                />
                <button
                  type="button"
                  onClick={() => productImageInputRef.current?.click()}
                  className="rounded-lg border border-slate-200 dark:border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  {imagePreview ? "Replace" : "Upload"}
                </button>
                {imagePreview && (
                  <button
                    type="button"
                    onClick={handleRemovePhoto}
                    className="rounded-lg px-2 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50"
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="e.g. Wireless Barcode Scanner"
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    SKU / Code (Optional)
                  </label>
                  <input
                    type="text"
                    value={form.sku}
                    onChange={(e) => setForm({ ...form, sku: e.target.value })}
                    placeholder="SKU-001"
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Category
                  </label>
                  <input
                    type="text"
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    placeholder="Hardware, Apparel, Consulting..."
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Selling Price (₹) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={form.selling_price}
                    onChange={(e) => setForm({ ...form, selling_price: e.target.value })}
                    placeholder="0.00"
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Cost Price (₹, Optional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={form.cost_price}
                    onChange={(e) => setForm({ ...form, cost_price: e.target.value })}
                    placeholder="0.00"
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    GST %
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={form.tax_percent}
                    onChange={(e) => setForm({ ...form, tax_percent: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Unit
                  </label>
                  <input
                    type="text"
                    required
                    value={form.unit}
                    onChange={(e) => setForm({ ...form, unit: e.target.value })}
                    placeholder="pcs, kg, box, hrs"
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>

                {form.item_type === "product" && (
                  <>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                        {editing ? "Current Stock" : "Initial Stock Quantity"}
                      </label>
                      <input
                        type="number"
                        min={0}
                        disabled={Boolean(editing)}
                        value={form.stock_quantity}
                        onChange={(e) => setForm({ ...form, stock_quantity: e.target.value })}
                        className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 disabled:opacity-60"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                        Low-Stock Alert Threshold
                      </label>
                      <input
                        type="number"
                        min={0}
                        value={form.min_stock_threshold}
                        onChange={(e) =>
                          setForm({ ...form, min_stock_threshold: e.target.value })
                        }
                        className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                      />
                    </div>
                  </>
                )}

                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Description (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-xl border border-slate-200 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-5 py-2 text-xs font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
                >
                  {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  {editing ? "Save Changes" : "Add to Catalogue"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

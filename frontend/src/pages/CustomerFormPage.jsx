import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Button from "../components/common/Button.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import Input from "../components/common/Input.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import Textarea from "../components/common/Textarea.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { createCustomer, getCustomer, updateCustomer } from "../services/customerService.js";
import { useToast } from "../context/ToastContext.jsx";
import { validateCustomerForm } from "../utils/validation.js";

const FIELDS = ["name", "email", "phone", "address", "notes"];

const EMPTY_FORM = {
  name: "",
  email: "",
  phone: "",
  address: "",
  notes: "",
};

const CANCEL_LINK_CLASSES =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2";

function buildPayload(form) {
  return Object.fromEntries(FIELDS.map((field) => [field, form[field].trim()]));
}

export default function CustomerFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const showToast = useToast();

  const [form, setForm] = useState(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const {
    data: customer,
    error: loadError,
    loading,
    refresh,
  } = useAsync(() => (isEdit ? getCustomer(id) : Promise.resolve(null)), [id, isEdit]);

  useEffect(() => {
    if (!customer) return;
    setForm({
      name: customer.name ?? "",
      email: customer.email ?? "",
      phone: customer.phone ?? "",
      address: customer.address ?? "",
      notes: customer.notes ?? "",
    });
  }, [customer]);

  const updateField = (field) => (event) => {
    const value = event.target.value;
    setForm((current) => ({ ...current, [field]: value }));
    setFieldErrors((current) => {
      if (!current[field]) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  };

  async function handleSubmit(event) {
    event.preventDefault();
    if (saving) return;

    const payload = buildPayload(form);
    const errors = validateCustomerForm(payload);
    setFieldErrors(errors);
    setFormError("");
    if (Object.keys(errors).length > 0) return;

    setSaving(true);
    try {
      if (isEdit) {
        await updateCustomer(id, payload);
        navigate(`/customers/${id}`);
        showToast("success", "Customer updated.");
      } else {
        const created = await createCustomer(payload);
        navigate(`/customers/${created.id}`);
        showToast("success", "Customer added.");
      }
    } catch (error) {
      setFieldErrors(error?.fieldErrors ?? {});
      setFormError(error?.message || "The customer could not be saved. Please try again.");
      setSaving(false);
    }
  }

  const title = isEdit ? "Edit customer" : "Add customer";
  const cancelTo = isEdit ? `/customers/${id}` : "/customers";

  let body;
  if (isEdit && loadError) {
    body = <ErrorState message={loadError.message} onRetry={refresh} />;
  } else if (isEdit && loading && !customer) {
    body = <LoadingState />;
  } else {
    body = (
      <form
        onSubmit={handleSubmit}
        noValidate
        className="space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <Input
          id="name"
          label="Name"
          required
          autoComplete="off"
          value={form.name}
          onChange={updateField("name")}
          error={fieldErrors.name}
        />

        <div className="grid gap-5 sm:grid-cols-2">
          <Input
            id="email"
            label="Email"
            type="email"
            value={form.email}
            onChange={updateField("email")}
            error={fieldErrors.email}
          />
          <Input
            id="phone"
            label="Phone"
            type="tel"
            value={form.phone}
            onChange={updateField("phone")}
            error={fieldErrors.phone}
          />
        </div>

        <Textarea
          id="address"
          label="Address"
          rows={2}
          value={form.address}
          onChange={updateField("address")}
          error={fieldErrors.address}
        />

        <Textarea
          id="notes"
          label="Notes"
          rows={3}
          value={form.notes}
          onChange={updateField("notes")}
          error={fieldErrors.notes}
        />

        {formError ? (
          <div
            role="alert"
            className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {formError}
          </div>
        ) : null}

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Link to={cancelTo} className={CANCEL_LINK_CLASSES}>
            Cancel
          </Link>
          <Button type="submit" loading={saving}>
            {isEdit ? "Save changes" : "Save customer"}
          </Button>
        </div>
      </form>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title={title} />
      {body}
    </div>
  );
}

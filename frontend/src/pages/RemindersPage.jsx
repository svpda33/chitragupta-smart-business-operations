import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Bell,
  Check,
  CheckCircle2,
  Clock,
  Copy,
  ExternalLink,
  Mail,
  MessageSquare,
  Phone,
  Send,
  Smartphone,
  User,
} from "lucide-react";
import Button from "../components/common/Button.jsx";
import EmptyState from "../components/common/EmptyState.jsx";
import ErrorState from "../components/common/ErrorState.jsx";
import LoadingState from "../components/common/LoadingState.jsx";
import Modal from "../components/common/Modal.jsx";
import PageHeader from "../components/common/PageHeader.jsx";
import SummaryItem from "../components/common/SummaryItem.jsx";
import Textarea from "../components/common/Textarea.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useToast } from "../context/ToastContext.jsx";
import { listReminders, logReminder } from "../services/reminderService.js";
import { formatDate } from "../utils/dates.js";
import { formatPaiseToRupees } from "../utils/formatMoney.js";

const CARD = "rounded-xl border border-slate-200 bg-white shadow-sm p-5";
const FILTER_OPTIONS = [
  { value: "all", label: "All Follow-ups" },
  { value: "overdue", label: "Overdue Only" },
  { value: "due_today", label: "Due Today" },
  { value: "upcoming", label: "Upcoming (Next 5 Days)" },
];

export default function RemindersPage() {
  const [filter, setFilter] = useState("all");
  const showToast = useToast();

  // Active Reminder Preview/Edit Modal state
  const [activeReminder, setActiveReminder] = useState(null);
  const [activeChannel, setActiveChannel] = useState("whatsapp"); // whatsapp, email, sms
  const [editedText, setEditedText] = useState("");
  const [emailSubject, setEmailSubject] = useState("");
  const [copiedChannel, setCopiedChannel] = useState(null);
  const [loggingReminder, setLoggingReminder] = useState(false);

  const { data: reminderData, loading, error, refresh } = useAsync(listReminders, []);

  if (loading && !reminderData) return <LoadingState label="Loading payment reminders queue…" />;
  if (error) return <ErrorState message={error.message} onRetry={refresh} />;
  if (!reminderData) return null;

  const {
    items = [],
    total_overdue_count = 0,
    total_upcoming_count = 0,
    total_outstanding_paise = 0,
  } = reminderData;

  const filteredItems = items.filter((item) => {
    if (filter === "overdue") {
      return ["first_overdue", "followup_overdue", "final_notice"].includes(item.urgency);
    }
    if (filter === "due_today") {
      return item.urgency === "due_today";
    }
    if (filter === "upcoming") {
      return item.urgency === "upcoming";
    }
    return true;
  });

  const handleOpenModal = (item, channel = "whatsapp") => {
    setActiveReminder(item);
    setActiveChannel(channel);
    if (channel === "whatsapp") {
      setEditedText(item.templates.whatsapp);
    } else if (channel === "email") {
      setEditedText(item.templates.email_body);
      setEmailSubject(item.templates.email_subject);
    } else {
      setEditedText(item.templates.sms);
    }
  };

  const handleSwitchChannel = (channel) => {
    if (!activeReminder) return;
    setActiveChannel(channel);
    if (channel === "whatsapp") {
      setEditedText(activeReminder.templates.whatsapp);
    } else if (channel === "email") {
      setEditedText(activeReminder.templates.email_body);
      setEmailSubject(activeReminder.templates.email_subject);
    } else {
      setEditedText(activeReminder.templates.sms);
    }
  };

  const handleCopy = async () => {
    let fullText = editedText;
    if (activeChannel === "email" && emailSubject) {
      fullText = `Subject: ${emailSubject}\n\n${editedText}`;
    }
    await navigator.clipboard.writeText(fullText);
    setCopiedChannel(activeChannel);
    showToast("success", "Message copied to clipboard!");
    setTimeout(() => setCopiedChannel(null), 2500);
  };

  const handleOpenWhatsApp = () => {
    if (!activeReminder) return;
    const phone = activeReminder.customer_phone ? activeReminder.customer_phone.replace(/[^\d+]/g, "") : "";
    const encoded = encodeURIComponent(editedText);
    const url = phone ? `https://wa.me/${phone}?text=${encoded}` : `https://wa.me/?text=${encoded}`;
    window.open(url, "_blank");
  };

  const handleOpenMailto = () => {
    if (!activeReminder) return;
    const email = activeReminder.customer_email || "";
    const subj = encodeURIComponent(emailSubject);
    const body = encodeURIComponent(editedText);
    window.location.href = `mailto:${email}?subject=${subj}&body=${body}`;
  };

  const handleLogSent = async () => {
    if (!activeReminder || loggingReminder) return;
    setLoggingReminder(true);
    try {
      await logReminder(activeReminder.invoice_id, {
        channel: activeChannel,
        note: `Manual dispatch via ${activeChannel.toUpperCase()}`,
      });
      showToast("success", "Reminder dispatch logged in audit history.");
      setActiveReminder(null);
      refresh();
    } catch (err) {
      showToast("error", err.message || "Failed to log reminder.");
    } finally {
      setLoggingReminder(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Assisted Payment Reminders"
        description="Assisted payment follow-ups for overdue and upcoming invoices with 1-click WhatsApp, email and SMS messages."
      />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryItem
          label="Total Actionable Receivables"
          value={formatPaiseToRupees(total_outstanding_paise)}
          tone="warning"
        />
        <SummaryItem
          label="Overdue Follow-ups"
          value={`${total_overdue_count} Invoices`}
          tone={total_overdue_count > 0 ? "danger" : "default"}
        />
        <SummaryItem
          label="Due Today & Upcoming"
          value={`${total_upcoming_count} Invoices`}
          tone="default"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setFilter(opt.value)}
            className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
              filter === opt.value
                ? "bg-brand-600 text-white shadow-xs"
                : "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {filteredItems.length === 0 ? (
        <EmptyState
          icon={CheckCircle2}
          title="All caught up!"
          message="No invoices match the selected reminder filter. All receivables are either paid or not yet due for follow-up."
          action={
            <Link
              to="/invoices"
              className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              View all invoices
            </Link>
          }
        />
      ) : (
        <div className="space-y-3">
          {filteredItems.map((item) => {
            const isOverdue = item.days_overdue > 0;
            const isFinal = item.urgency === "final_notice";
            const isFollowup = item.urgency === "followup_overdue";

            const badgeBg = isFinal
              ? "bg-red-100 text-red-800 border-red-200"
              : isFollowup
              ? "bg-orange-100 text-orange-800 border-orange-200"
              : isOverdue
              ? "bg-amber-100 text-amber-800 border-amber-200"
              : item.urgency === "due_today"
              ? "bg-blue-100 text-blue-800 border-blue-200"
              : "bg-slate-100 text-slate-800 border-slate-200";

            return (
              <div
                key={item.invoice_id}
                className={`${CARD} hover:border-slate-300 transition-all flex flex-col lg:flex-row lg:items-center justify-between gap-4`}
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm">
                      <Link to={`/invoices/${item.invoice_id}`} className="hover:text-brand-600 hover:underline">
                        {item.invoice_number}
                      </Link>
                    </span>
                    <span className="text-slate-400">•</span>
                    <span className="font-semibold text-slate-800 text-sm">{item.customer_name}</span>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold border ${badgeBg}`}>
                      {item.urgency_label}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600">
                    <span className="flex items-center gap-1 font-semibold text-brand-700">
                      Outstanding: {formatPaiseToRupees(item.outstanding_paise)}
                    </span>
                    <span>Due Date: {formatDate(item.due_date)}</span>
                    {item.customer_phone && (
                      <span className="flex items-center gap-1">
                        <Phone className="h-3 w-3 text-slate-400" />
                        {item.customer_phone}
                      </span>
                    )}
                    {item.customer_email && (
                      <span className="flex items-center gap-1">
                        <Mail className="h-3 w-3 text-slate-400" />
                        {item.customer_email}
                      </span>
                    )}
                    {item.last_reminded_at && (
                      <span className="text-emerald-700 font-medium">
                        Last reminded: {formatDate(item.last_reminded_at)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap items-center gap-2 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100">
                  <button
                    type="button"
                    onClick={() => handleOpenModal(item, "whatsapp")}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700 shadow-xs"
                  >
                    <MessageSquare className="h-3.5 w-3.5" />
                    WhatsApp
                  </button>
                  <button
                    type="button"
                    onClick={() => handleOpenModal(item, "email")}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    <Mail className="h-3.5 w-3.5" />
                    Email
                  </button>
                  <button
                    type="button"
                    onClick={() => handleOpenModal(item, "sms")}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    <Smartphone className="h-3.5 w-3.5" />
                    SMS
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Reminder Preview & Copy/Send Modal */}
      {activeReminder && (
        <Modal
          title={`Assisted Payment Reminder — ${activeReminder.invoice_number}`}
          open={Boolean(activeReminder)}
          onClose={() => setActiveReminder(null)}
        >
          <div className="space-y-4">
            {/* Invoice summary pill */}
            <div className="rounded-lg bg-slate-50 p-3 border border-slate-200 text-xs flex justify-between items-center">
              <div>
                <span className="font-semibold text-slate-900">{activeReminder.customer_name}</span>
                <span className="text-slate-500 ml-2">({activeReminder.invoice_number})</span>
              </div>
              <div className="font-bold text-brand-700">
                Amount Due: {formatPaiseToRupees(activeReminder.outstanding_paise)}
              </div>
            </div>

            {/* Channel Tabs */}
            <div className="flex border-b border-slate-200">
              <button
                type="button"
                onClick={() => handleSwitchChannel("whatsapp")}
                className={`py-2 px-4 text-xs font-semibold border-b-2 transition-colors ${
                  activeChannel === "whatsapp"
                    ? "border-emerald-600 text-emerald-700"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                WhatsApp Message
              </button>
              <button
                type="button"
                onClick={() => handleSwitchChannel("email")}
                className={`py-2 px-4 text-xs font-semibold border-b-2 transition-colors ${
                  activeChannel === "email"
                    ? "border-brand-600 text-brand-700"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                Email Message
              </button>
              <button
                type="button"
                onClick={() => handleSwitchChannel("sms")}
                className={`py-2 px-4 text-xs font-semibold border-b-2 transition-colors ${
                  activeChannel === "sms"
                    ? "border-indigo-600 text-indigo-700"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                SMS Message
              </button>
            </div>

            {/* Editable Content */}
            {activeChannel === "email" && (
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Subject Line
                </label>
                <input
                  type="text"
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 focus:border-brand-500 focus:outline-none"
                />
              </div>
            )}

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Message Body (Customizable)
                </label>
                <span className="text-[11px] text-slate-400">Feel free to personalize before copying</span>
              </div>
              <Textarea
                rows={9}
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="font-mono text-xs leading-relaxed"
              />
            </div>

            {/* Quick Actions Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 border-t border-slate-200">
              <div className="flex items-center gap-2">
                <Button variant="secondary" onClick={handleCopy}>
                  {copiedChannel === activeChannel ? (
                    <>
                      <Check className="h-4 w-4 text-emerald-600" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy Message
                    </>
                  )}
                </Button>

                {activeChannel === "whatsapp" && (
                  <button
                    type="button"
                    onClick={handleOpenWhatsApp}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-700"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    Open in WhatsApp
                  </button>
                )}

                {activeChannel === "email" && (
                  <button
                    type="button"
                    onClick={handleOpenMailto}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-2 text-xs font-medium text-white hover:bg-brand-700"
                  >
                    <Mail className="h-3.5 w-3.5" />
                    Open Mail Client
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2">
                <Button variant="secondary" onClick={() => setActiveReminder(null)}>
                  Close
                </Button>
                <Button
                  onClick={handleLogSent}
                  loading={loggingReminder}
                  className="bg-slate-900 text-white hover:bg-slate-800"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Mark as Reminded
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

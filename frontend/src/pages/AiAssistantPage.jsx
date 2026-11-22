import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  Database,
  History,
  Loader2,
  MessageSquare,
  Mic,
  MicOff,
  PanelLeftClose,
  PanelLeftOpen,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Square,
  Trash2,
  User,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import Button from "../components/common/Button.jsx";
import ConfirmDialog from "../components/common/ConfirmDialog.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { useDebouncedValue } from "../hooks/useDebouncedValue.js";
import { useVoiceAssistant } from "../hooks/useVoiceAssistant.js";
import { useToast } from "../context/ToastContext.jsx";
import {
  deleteConversation,
  getAiStatus,
  getConversation,
  listConversations,
  renameConversation,
  sendChatMessage,
} from "../services/aiService.js";

const ACTIVE_CONV_KEY = "chitragupta_active_ai_conversation";
const AI_HISTORY_SIDEBAR_KEY = "chitragupta_ai_history_sidebar_open";

const SUGGESTED_QUESTIONS = [
  "Give me a complete financial health summary.",
  "Who owes me the most money?",
  "Which invoices need immediate attention?",
  "Can I afford a ₹25,000 expense next week?",
  "What happens if my biggest customer pays 15 days late?",
  "Which customers should I follow up with today?",
];

const KIND_STYLES = {
  actual:
    "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30",
  forecast:
    "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-500/15 dark:text-blue-300 dark:border-blue-500/30",
  simulation:
    "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-500/15 dark:text-purple-300 dark:border-purple-500/30",
};

const KIND_LABELS = {
  actual: "Actual",
  forecast: "Forecast",
  simulation: "Simulation",
};

function formatTimestamp(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderInlineBold(text) {
  const parts = String(text || "").split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} className="font-semibold text-slate-900 dark:text-slate-100">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={idx}>{part}</span>;
  });
}

function FormattedReply({ text }) {
  const lines = String(text || "").split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();
    if (!line) {
      i += 1;
      continue;
    }

    // Markdown table detection
    if (line.startsWith("|") && i + 1 < lines.length && lines[i + 1].trim().startsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i].trim());
        i += 1;
      }
      const rows = tableLines
        .filter((l) => !/^\|[\s:-]+\|$/.test(l.replace(/\s+/g, "")))
        .map((l) =>
          l
            .split("|")
            .slice(1, -1)
            .map((cell) => cell.trim())
        );
      if (rows.length > 0) {
        blocks.push({ type: "table", header: rows[0], body: rows.slice(1) });
      }
      continue;
    }

    if (line.startsWith("### ")) {
      blocks.push({ type: "h4", text: line.slice(4) });
    } else if (line.startsWith("## ")) {
      blocks.push({ type: "h3", text: line.slice(3) });
    } else if (line.startsWith("- ") || line.startsWith("* ") || line.startsWith("• ")) {
      blocks.push({ type: "bullet", text: line.slice(2) });
    } else {
      blocks.push({ type: "p", text: line });
    }
    i += 1;
  }

  return (
    <div className="space-y-1.5 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
      {blocks.map((block, idx) => {
        if (block.type === "h3") {
          return (
            <h3 key={idx} className="pt-2 text-base font-semibold text-slate-900 dark:text-slate-100">
              {renderInlineBold(block.text)}
            </h3>
          );
        }
        if (block.type === "h4") {
          return (
            <h4 key={idx} className="pt-1.5 text-sm font-semibold text-slate-900 dark:text-slate-100">
              {renderInlineBold(block.text)}
            </h4>
          );
        }
        if (block.type === "bullet") {
          return (
            <div key={idx} className="flex items-start gap-2 pl-1">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600 dark:bg-brand-400" />
              <span>{renderInlineBold(block.text)}</span>
            </div>
          );
        }
        if (block.type === "table") {
          return (
            <div
              key={idx}
              className="my-2 overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700"
            >
              <table className="min-w-full divide-y divide-slate-200 text-xs dark:divide-slate-700">
                <thead className="bg-slate-100/80 dark:bg-slate-800">
                  <tr>
                    {block.header.map((col, ci) => (
                      <th
                        key={ci}
                        className="px-3 py-2 text-left font-semibold text-slate-700 dark:text-slate-200"
                      >
                        {renderInlineBold(col)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-800 dark:bg-slate-900/50">
                  {block.body.map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-3 py-2 tabular-nums text-slate-700 dark:text-slate-300">
                          {renderInlineBold(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return <p key={idx}>{renderInlineBold(block.text)}</p>;
      })}
    </div>
  );
}

function normalizeServerMessage(m) {
  return {
    id: `msg-${m.id}`,
    role: m.role,
    content: m.content,
    model: m.model,
    asOfDate: m.as_of_date,
    toolsUsed: m.tools_used ?? [],
    evidence: m.evidence ?? [],
    suggestedActions: m.suggested_actions ?? [],
    createdAt: m.created_at,
  };
}

export default function AiAssistantPage() {
  const showToast = useToast();
  const statusState = useAsync(getAiStatus, []);
  const status = statusState.data;

  const voice = useVoiceAssistant();

  // Persistent conversation sidebar state
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearch = useDebouncedValue(searchQuery, 250);
  const [conversations, setConversations] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);
  const [historySidebarOpen, setHistorySidebarOpen] = useState(() => {
    try {
      const saved = localStorage.getItem(AI_HISTORY_SIDEBAR_KEY);
      return saved === null ? true : saved === "true";
    } catch {
      return true;
    }
  });

  const toggleDesktopHistorySidebar = useCallback(() => {
    setHistorySidebarOpen((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(AI_HISTORY_SIDEBAR_KEY, String(next));
      } catch {
        // ignore storage errors
      }
      return next;
    });
  }, []);

  // Active conversation state
  const [activeConvId, setActiveConvId] = useState(() => {
    try {
      const saved = localStorage.getItem(ACTIVE_CONV_KEY);
      return saved && /^\d+$/.test(saved) ? Number(saved) : null;
    } catch {
      return null;
    }
  });
  const [activeTitle, setActiveTitle] = useState("New conversation");
  const [messages, setMessages] = useState([]);
  const [loadingConv, setLoadingConv] = useState(false);

  // Rename & delete state
  const [renamingId, setRenamingId] = useState(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Chat composer state
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [lastError, setLastError] = useState(null);
  const [lastPrompt, setLastPrompt] = useState("");
  const bottomRef = useRef(null);

  const persistActiveConvId = useCallback((id) => {
    setActiveConvId(id);
    try {
      if (id != null) localStorage.setItem(ACTIVE_CONV_KEY, String(id));
      else localStorage.removeItem(ACTIVE_CONV_KEY);
    } catch {
      // ignore storage errors
    }
  }, []);

  const refreshConversations = useCallback(async (search = "") => {
    setLoadingList(true);
    try {
      const items = await listConversations(search);
      setConversations(items ?? []);
    } catch {
      // silent list failure; chat remains usable
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    refreshConversations(debouncedSearch);
  }, [debouncedSearch, refreshConversations]);

  // Load persisted active conversation on initial mount
  const openConversation = useCallback(
    async (convId) => {
      if (!convId) return;
      voice.stopSpeaking();
      setLoadingConv(true);
      setLastError(null);
      try {
        const detail = await getConversation(convId);
        persistActiveConvId(detail.id);
        setActiveTitle(detail.title);
        setMessages((detail.messages ?? []).map(normalizeServerMessage));
        setHistoryDrawerOpen(false);
      } catch {
        // Conversation may have been deleted; start fresh
        persistActiveConvId(null);
        setActiveTitle("New conversation");
        setMessages([]);
      } finally {
        setLoadingConv(false);
      }
    },
    [persistActiveConvId, voice]
  );

  useEffect(() => {
    if (activeConvId != null) {
      openConversation(activeConvId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const handleNewConversation = () => {
    voice.stopSpeaking();
    persistActiveConvId(null);
    setActiveTitle("New conversation");
    setMessages([]);
    setLastError(null);
    setLastPrompt("");
    setHistoryDrawerOpen(false);
  };

  const handleSend = async (promptText) => {
    const trimmed = String(promptText ?? input).trim();
    if (!trimmed || sending) return;

    voice.stopListening();
    voice.stopSpeaking();

    const optimisticUserMsg = {
      id: `temp-user-${Date.now()}`,
      role: "user",
      content: trimmed,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimisticUserMsg]);
    setInput("");
    setLastError(null);
    setLastPrompt(trimmed);
    setSending(true);

    try {
      const data = await sendChatMessage(trimmed, {
        conversationId: activeConvId,
        history:
          activeConvId == null
            ? messages.slice(-8).map((m) => ({ role: m.role, content: m.content }))
            : [],
      });

      const assistantMsg = {
        id: data.message_id ? `msg-${data.message_id}` : `assistant-${Date.now()}`,
        role: "assistant",
        content: data.reply,
        model: data.model,
        asOfDate: data.as_of_date,
        toolsUsed: data.tools_used ?? [],
        evidence: data.evidence ?? [],
        suggestedActions: data.suggested_actions ?? [],
        createdAt: data.created_at || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (data.conversation_id) {
        persistActiveConvId(data.conversation_id);
      }
      if (data.conversation_title) {
        setActiveTitle(data.conversation_title);
      }

      refreshConversations(debouncedSearch);

      if (voice.autoRead && voice.ttsSupported) {
        voice.speak(assistantMsg.id, assistantMsg.content);
      }
    } catch (err) {
      setLastError(err?.message || "Failed to reach the Finance Copilot. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const handleRetry = () => {
    if (!lastPrompt || sending) return;
    setMessages((prev) => {
      if (prev.length > 0 && prev[prev.length - 1].role === "user") {
        return prev.slice(0, -1);
      }
      return prev;
    });
    setLastError(null);
    handleSend(lastPrompt);
  };

  const handleStartRename = (conv, event) => {
    event.stopPropagation();
    setRenamingId(conv.id);
    setRenameDraft(conv.title);
  };

  const handleSaveRename = async (convId) => {
    const trimmed = renameDraft.trim();
    if (!trimmed) {
      setRenamingId(null);
      return;
    }
    try {
      const updated = await renameConversation(convId, trimmed);
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, title: updated.title } : c))
      );
      if (activeConvId === convId) {
        setActiveTitle(updated.title);
      }
      showToast("success", "Conversation renamed.");
    } catch (err) {
      showToast("error", err?.message || "Could not rename conversation.");
    } finally {
      setRenamingId(null);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget || deleting) return;
    setDeleting(true);
    try {
      await deleteConversation(deleteTarget.id);
      setConversations((prev) => prev.filter((c) => c.id !== deleteTarget.id));
      if (activeConvId === deleteTarget.id) {
        handleNewConversation();
      }
      showToast("success", "Conversation deleted.");
      setDeleteTarget(null);
    } catch (err) {
      showToast("error", err?.message || "Could not delete conversation.");
    } finally {
      setDeleting(false);
    }
  };

  const handleMicToggle = () => {
    if (voice.voiceState === "listening") {
      voice.stopListening();
    } else {
      voice.startListening((transcript) => {
        setInput(transcript);
      });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const historySidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 p-3 dark:border-slate-800">
        <Button onClick={handleNewConversation} className="w-full justify-center py-2 text-xs">
          <Plus className="h-4 w-4" />
          New Conversation
        </Button>
      </div>

      <div className="border-b border-slate-200 p-3 dark:border-slate-800">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations…"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-3 text-xs text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
        </div>
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto p-2">
        {loadingList && conversations.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">Loading history…</div>
        ) : conversations.length === 0 ? (
          <div className="px-3 py-8 text-center text-xs text-slate-400">
            {searchQuery.trim()
              ? "No matching conversations."
              : "Your saved conversations will appear here."}
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.id === activeConvId;
            const isRenaming = renamingId === conv.id;
            return (
              <div
                key={conv.id}
                onClick={() => !isRenaming && openConversation(conv.id)}
                className={`group flex cursor-pointer items-start justify-between gap-2 rounded-xl px-3 py-2.5 transition-colors ${
                  isActive
                    ? "bg-brand-50 text-brand-800 ring-1 ring-brand-200/80 dark:bg-brand-500/15 dark:text-brand-200 dark:ring-brand-500/30"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/70"
                }`}
              >
                <div className="min-w-0 flex-1">
                  {isRenaming ? (
                    <div
                      className="flex items-center gap-1"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="text"
                        autoFocus
                        value={renameDraft}
                        onChange={(e) => setRenameDraft(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleSaveRename(conv.id);
                          if (e.key === "Escape") setRenamingId(null);
                        }}
                        className="w-full rounded-md border border-brand-400 bg-white px-2 py-0.5 text-xs text-slate-900 focus:outline-none dark:bg-slate-900 dark:text-slate-100"
                      />
                      <button
                        type="button"
                        onClick={() => handleSaveRename(conv.id)}
                        aria-label="Save title"
                        className="rounded p-1 text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400"
                      >
                        <Check className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-1.5">
                        <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-60" />
                        <p className="truncate text-xs font-semibold">{conv.title}</p>
                      </div>
                      <p className="mt-0.5 text-[10px] text-slate-400 dark:text-slate-500">
                        {formatTimestamp(conv.updated_at)} • {conv.message_count} msg
                      </p>
                    </>
                  )}
                </div>

                {!isRenaming && (
                  <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                    <button
                      type="button"
                      onClick={(e) => handleStartRename(conv, e)}
                      aria-label={`Rename ${conv.title}`}
                      className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-700 dark:hover:text-slate-200"
                    >
                      <Pencil className="h-3 w-3" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteTarget(conv);
                      }}
                      aria-label={`Delete ${conv.title}`}
                      className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-500/20 dark:hover:text-red-400"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Top Status & Controls Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <h1 className="truncate text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              AI Finance Copilot
            </h1>
            {status && (
              <span
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                  status.configured
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/15 dark:text-emerald-300"
                    : "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/15 dark:text-amber-300"
                }`}
              >
                {status.configured ? (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Gemini Ready
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3.5 w-3.5" />
                    API Key Required
                  </>
                )}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Grounded in verified Chitragupta ledger figures, forecasts, and non-destructive simulations • History saved in SQLite
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Desktop Independent AI History Sidebar Toggle */}
          <button
            type="button"
            onClick={toggleDesktopHistorySidebar}
            aria-expanded={historySidebarOpen}
            aria-label={historySidebarOpen ? "Collapse chat history sidebar" : "Expand chat history sidebar"}
            className="hidden lg:inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            {historySidebarOpen ? (
              <>
                <PanelLeftClose className="h-3.5 w-3.5" />
                Hide History
              </>
            ) : (
              <>
                <PanelLeftOpen className="h-3.5 w-3.5" />
                Show History ({conversations.length})
              </>
            )}
          </button>

          {/* Mobile History Toggle */}
          <Button
            variant="secondary"
            onClick={() => setHistoryDrawerOpen((v) => !v)}
            className="py-2 text-xs lg:hidden"
          >
            <History className="h-3.5 w-3.5" />
            History ({conversations.length})
          </Button>

          {/* Optional Auto-Read Replies Toggle (off by default) */}
          {voice.ttsSupported && (
            <button
              type="button"
              onClick={() => {
                const next = !voice.autoRead;
                voice.setAutoRead(next);
                if (!next) voice.stopSpeaking();
              }}
              aria-pressed={voice.autoRead}
              className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-medium transition-colors ${
                voice.autoRead
                  ? "border-brand-300 bg-brand-50 text-brand-700 dark:border-brand-500/40 dark:bg-brand-500/15 dark:text-brand-300"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              }`}
              title="Automatically read new AI replies aloud"
            >
              {voice.autoRead ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
              Auto-read: {voice.autoRead ? "On" : "Off"}
            </button>
          )}
        </div>
      </div>

      {/* Setup Banner if API key missing */}
      {status && !status.configured && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50/80 p-4 text-xs text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <div>
              <p className="font-semibold">Gemini API key not configured</p>
              <p className="mt-0.5 opacity-90">
                Add <code className="rounded bg-amber-100 px-1 py-0.5 font-mono dark:bg-amber-900/50">GEMINI_API_KEY</code> to{" "}
                <code className="rounded bg-amber-100 px-1 py-0.5 font-mono dark:bg-amber-900/50">backend/.env</code> and restart the backend server.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Split-Pane Copilot Workspace */}
      <div className="grid min-h-[620px] grid-cols-1 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xs dark:border-slate-800 dark:bg-[#111827] lg:grid-cols-12">
        {/* Desktop Persistent History Sidebar (Independently Collapsible) */}
        {historySidebarOpen && (
          <aside className="hidden border-r border-slate-200 dark:border-slate-800 lg:col-span-3 lg:block">
            {historySidebarContent}
          </aside>
        )}

        {/* Mobile History Drawer */}
        {historyDrawerOpen && (
          <div className="border-b border-slate-200 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-900/50 lg:hidden">
            <div className="flex items-center justify-between px-3 pt-2">
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                Saved Conversations
              </span>
              <button
                type="button"
                onClick={() => setHistoryDrawerOpen(false)}
                className="rounded p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="max-h-72 overflow-y-auto">{historySidebarContent}</div>
          </div>
        )}

        {/* Right Chat Area */}
        <div className={`flex flex-col ${historySidebarOpen ? "lg:col-span-9" : "lg:col-span-12"}`}>
          {/* Active Conversation Subheader */}
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3 dark:border-slate-800">
            <div className="flex min-w-0 items-center gap-2">
              <ShieldCheck className="h-4 w-4 shrink-0 text-brand-600 dark:text-brand-400" />
              <span className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                {activeTitle}
              </span>
            </div>
            <span className="hidden text-[11px] text-slate-400 sm:inline">
              Read-only tools • Integer-paise Python math
            </span>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 space-y-5 overflow-y-auto p-5">
            {loadingConv ? (
              <div className="flex items-center justify-center gap-2 py-16 text-sm text-slate-500">
                <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
                Loading conversation…
              </div>
            ) : messages.length === 0 ? (
              <div className="py-6 text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
                  <Sparkles className="h-6 w-6" />
                </div>
                <h2 className="mt-3 text-base font-semibold text-slate-900 dark:text-slate-100">
                  Ask your Finance Copilot anything
                </h2>
                <p className="mx-auto mt-1 max-w-lg text-xs text-slate-500 dark:text-slate-400">
                  Type or use the microphone button to ask about receivables, overdue invoices, cash runway, upcoming expenses, or delayed payment what-ifs.
                </p>

                <div className="mt-6 grid grid-cols-1 gap-2.5 text-left sm:grid-cols-2">
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      type="button"
                      disabled={sending}
                      onClick={() => handleSend(q)}
                      className="group flex items-center justify-between gap-2 rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-xs font-medium text-slate-700 transition-all hover:border-brand-300 hover:bg-brand-50/60 hover:text-brand-800 disabled:opacity-50 dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-300 dark:hover:border-brand-500/40 dark:hover:bg-brand-500/10 dark:hover:text-brand-200"
                    >
                      <span>{q}</span>
                      <ArrowRight className="h-3.5 w-3.5 shrink-0 text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-600" />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) =>
                msg.role === "user" ? (
                  <div key={msg.id} className="flex justify-end">
                    <div className="flex max-w-[85%] items-start gap-2.5">
                      <div className="space-y-1 text-right">
                        <div className="rounded-2xl rounded-tr-sm bg-brand-600 px-4 py-2.5 text-left text-sm text-white shadow-2xs">
                          {msg.content}
                        </div>
                        {msg.createdAt && (
                          <p className="text-[10px] text-slate-400">{formatTimestamp(msg.createdAt)}</p>
                        )}
                      </div>
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200">
                        <User className="h-4 w-4" />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div key={msg.id} className="flex justify-start">
                    <div className="flex max-w-[94%] items-start gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-500/30 dark:bg-brand-500/15 dark:text-brand-300">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="flex-1 space-y-3 rounded-2xl rounded-tl-sm border border-slate-200 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-900/60">
                        <FormattedReply text={msg.content} />

                        {/* Verified Figures Evidence */}
                        {msg.evidence && msg.evidence.length > 0 && (
                          <div className="border-t border-slate-200/80 pt-3 dark:border-slate-800">
                            <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                              <Database className="h-3.5 w-3.5" />
                              Verified Figures Used
                            </div>
                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
                              {msg.evidence.map((ev, i) => (
                                <div
                                  key={i}
                                  className="rounded-xl border border-slate-200 bg-white p-2.5 dark:border-slate-800 dark:bg-[#111827]"
                                >
                                  <div className="flex items-center justify-between gap-1">
                                    <span className="truncate text-[11px] font-medium text-slate-500 dark:text-slate-400">
                                      {ev.label}
                                    </span>
                                    <span
                                      className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${
                                        KIND_STYLES[ev.kind] || KIND_STYLES.actual
                                      }`}
                                    >
                                      {KIND_LABELS[ev.kind] || "Actual"}
                                    </span>
                                  </div>
                                  <div className="mt-1 text-sm font-bold tabular-nums text-slate-900 dark:text-slate-100">
                                    {ev.value}
                                  </div>
                                  {ev.note && (
                                    <div className="mt-0.5 truncate text-[11px] text-slate-500 dark:text-slate-400">
                                      {ev.note}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Quick Actions */}
                        {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                          <div className="flex flex-wrap items-center gap-2 border-t border-slate-200/80 pt-3 dark:border-slate-800">
                            {msg.suggestedActions.map((act) => (
                              <Link
                                key={act.url}
                                to={act.url}
                                className="inline-flex items-center gap-1 rounded-lg border border-brand-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-brand-700 hover:bg-brand-50 dark:border-brand-500/30 dark:bg-slate-800 dark:text-brand-300 dark:hover:bg-brand-500/15"
                              >
                                {act.label}
                                <ArrowRight className="h-3 w-3" />
                              </Link>
                            ))}
                          </div>
                        )}

                        {/* Footer: Metadata + Voice Read-Aloud Controls */}
                        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200/60 pt-2.5 text-[11px] text-slate-400 dark:border-slate-800">
                          <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
                            {msg.createdAt && <span>{formatTimestamp(msg.createdAt)}</span>}
                            {msg.asOfDate && (
                              <>
                                <span>•</span>
                                <span>As of {msg.asOfDate}</span>
                              </>
                            )}
                            {msg.model && (
                              <>
                                <span>•</span>
                                <span>{msg.model}</span>
                              </>
                            )}
                            {msg.toolsUsed && msg.toolsUsed.length > 0 && (
                              <>
                                <span>•</span>
                                <span>Tools: {msg.toolsUsed.join(", ")}</span>
                              </>
                            )}
                          </div>

                          {voice.ttsSupported && (
                            <button
                              type="button"
                              onClick={() =>
                                voice.speakingId === msg.id
                                  ? voice.stopSpeaking()
                                  : voice.speak(msg.id, msg.content)
                              }
                              className={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-medium transition-colors ${
                                voice.speakingId === msg.id
                                  ? "bg-brand-600 text-white"
                                  : "text-slate-500 hover:bg-slate-200/70 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                              }`}
                            >
                              {voice.speakingId === msg.id ? (
                                <>
                                  <Square className="h-3 w-3 fill-current" />
                                  Stop speaking
                                </>
                              ) : (
                                <>
                                  <Volume2 className="h-3.5 w-3.5" />
                                  Listen
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              )
            )}

            {/* Thinking Indicator */}
            {sending && (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-500/30 dark:bg-brand-500/15 dark:text-brand-300">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-xs font-medium text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                  Running financial tools & preparing verified insights…
                </div>
              </div>
            )}

            {/* Error & Retry */}
            {lastError && (
              <div className="rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200">
                <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
                    <span>{lastError}</span>
                  </div>
                  <Button variant="secondary" onClick={handleRetry} disabled={sending}>
                    <RefreshCw className="h-3.5 w-3.5" />
                    Retry
                  </Button>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Composer Bar with Voice Input Controls */}
          <div className="border-t border-slate-200 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-900/60">
            {/* Voice status feedback pill */}
            {(voice.voiceState === "listening" ||
              voice.voiceState === "processing" ||
              voice.voiceError) && (
              <div className="mb-2 flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-800">
                <span className="flex items-center gap-2 font-medium text-slate-700 dark:text-slate-200">
                  {voice.voiceState === "listening" && (
                    <>
                      <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
                      Listening… speak your financial question
                    </>
                  )}
                  {voice.voiceState === "processing" && (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-600" />
                      Processing speech… review or edit below before sending
                    </>
                  )}
                  {voice.voiceError && (
                    <span className="text-amber-700 dark:text-amber-300">{voice.voiceError}</span>
                  )}
                </span>
                {voice.voiceState === "listening" && (
                  <button
                    type="button"
                    onClick={voice.stopListening}
                    className="text-xs font-semibold text-red-600 hover:underline dark:text-red-400"
                  >
                    Stop
                  </button>
                )}
              </div>
            )}

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-end gap-2"
            >
              {/* Microphone Voice Input Button */}
              <button
                type="button"
                onClick={handleMicToggle}
                disabled={sending || !voice.sttSupported}
                title={
                  !voice.sttSupported
                    ? "Voice input unavailable in this browser"
                    : voice.voiceState === "listening"
                    ? "Stop listening"
                    : voice.voiceState === "denied"
                    ? "Microphone permission denied"
                    : "Speak your question (browser voice input)"
                }
                aria-label={
                  voice.voiceState === "listening" ? "Stop voice input" : "Start voice input"
                }
                className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border transition-colors ${
                  voice.voiceState === "listening"
                    ? "border-red-500 bg-red-600 text-white shadow-sm"
                    : !voice.sttSupported
                    ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500"
                    : "border-slate-300 bg-white text-slate-600 hover:border-brand-400 hover:text-brand-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:text-brand-300"
                }`}
              >
                {voice.voiceState === "listening" || !voice.sttSupported ? (
                  <MicOff className="h-4 w-4" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </button>

              <textarea
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={sending}
                placeholder="Ask about receivables, overdue invoices, 30–90 day cash flow, or delayed payment what-ifs…"
                className="block flex-1 resize-none rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500"
              />

              <Button type="submit" loading={sending} disabled={!input.trim() || sending} className="h-11">
                <Send className="h-4 w-4" />
                Ask
              </Button>
            </form>
          </div>
        </div>
      </div>

      {/* Delete Conversation Confirmation Modal */}
      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete conversation?"
        message={`This will permanently delete "${deleteTarget?.title || ""}" and all its saved messages.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}

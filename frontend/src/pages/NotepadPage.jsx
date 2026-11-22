import { useCallback, useEffect, useRef, useState } from "react";
import {
  Check,
  CheckSquare,
  Loader2,
  Pin,
  Plus,
  Search,
  Square,
  StickyNote,
  Trash2,
  X,
} from "lucide-react";
import {
  createNote,
  deleteNote,
  listNotes,
  updateNote,
} from "../services/noteService.js";
import { formatDate } from "../utils/dates.js";
import { useToast } from "../context/ToastContext.jsx";

const CATEGORIES = ["General", "Operations", "Suppliers", "Customers", "Finance", "Ideas"];

export default function NotepadPage() {
  const showToast = useToast();
  const addToast = useCallback((msg, type = "info") => showToast(type, msg), [showToast]);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  // Active editor fields
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("General");
  const [content, setContent] = useState("");
  const [isPinned, setIsPinned] = useState(false);
  const [checklist, setChecklist] = useState([]);
  const [newTaskText, setNewTaskText] = useState("");
  const [saveState, setSaveState] = useState("idle"); // idle | saving | saved

  const saveTimerRef = useRef(null);
  const skipNextAutoSaveRef = useRef(true);

  const loadNotes = useCallback(
    async (keepSelection = true) => {
      try {
        const params = search.trim() ? { search: search.trim() } : {};
        const data = await listNotes(params);
        const list = Array.isArray(data) ? data : [];
        setNotes(list);
        if (!keepSelection || !list.some((n) => n.id === selectedId)) {
          if (list.length > 0) {
            selectNoteObject(list[0]);
          } else {
            setSelectedId(null);
          }
        }
      } catch (err) {
        addToast(err.message || "Could not load notes.", "error");
      } finally {
        setLoading(false);
      }
    },
    [search, selectedId, addToast]
  );

  useEffect(() => {
    const t = setTimeout(() => loadNotes(true), 200);
    return () => clearTimeout(t);
  }, [search]); // eslint-disable-line react-hooks/exhaustive-deps

  function selectNoteObject(n) {
    skipNextAutoSaveRef.current = true;
    setSelectedId(n.id);
    setTitle(n.title || "");
    setCategory(n.category || "General");
    setContent(n.content || "");
    setIsPinned(Boolean(n.is_pinned));
    setChecklist(Array.isArray(n.checklist) ? n.checklist : []);
    setSaveState("idle");
  }

  async function handleNewNote() {
    try {
      const created = await createNote({
        title: "Untitled Note",
        category: "General",
        content: "",
        is_pinned: false,
        checklist: [],
      });
      setNotes((prev) => [created, ...prev]);
      selectNoteObject(created);
      addToast("New note created.", "success");
    } catch (err) {
      addToast(err.message || "Could not create note.", "error");
    }
  }

  const persistCurrent = useCallback(
    async (override = {}) => {
      if (!selectedId) return;
      setSaveState("saving");
      try {
        const payload = {
          title: (override.title ?? title).trim() || "Untitled Note",
          category: override.category ?? category,
          content: override.content ?? content,
          is_pinned: override.is_pinned ?? isPinned,
          checklist: override.checklist ?? checklist,
        };
        const updated = await updateNote(selectedId, payload);
        setNotes((prev) =>
          prev
            .map((n) => (n.id === updated.id ? updated : n))
            .sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned))
        );
        setSaveState("saved");
      } catch (err) {
        setSaveState("idle");
        addToast(err.message || "Auto-save failed.", "error");
      }
    },
    [selectedId, title, category, content, isPinned, checklist, addToast]
  );

  // Debounced auto-save when editing
  useEffect(() => {
    if (!selectedId) return;
    if (skipNextAutoSaveRef.current) {
      skipNextAutoSaveRef.current = false;
      return;
    }
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      persistCurrent();
    }, 600);
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, [title, category, content, isPinned, checklist, selectedId, persistCurrent]);

  function addChecklistItem(e) {
    e.preventDefault();
    if (!newTaskText.trim()) return;
    const next = [
      ...checklist,
      { id: String(Date.now()), text: newTaskText.trim(), done: false },
    ];
    setChecklist(next);
    setNewTaskText("");
  }

  function toggleTask(id) {
    setChecklist((prev) => prev.map((t) => (t.id === id ? { ...t, done: !t.done } : t)));
  }

  function removeTask(id) {
    setChecklist((prev) => prev.filter((t) => t.id !== id));
  }

  async function handleDelete() {
    if (!selectedId) return;
    if (!window.confirm("Delete this note permanently?")) return;
    try {
      await deleteNote(selectedId);
      const remaining = notes.filter((n) => n.id !== selectedId);
      setNotes(remaining);
      if (remaining.length > 0) {
        selectNoteObject(remaining[0]);
      } else {
        setSelectedId(null);
      }
      addToast("Note deleted.", "success");
    } catch (err) {
      addToast(err.message || "Could not delete note.", "error");
    }
  }

  const activeNote = notes.find((n) => n.id === selectedId) || null;

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-extrabold text-slate-900 dark:text-white">
            Business Notepad
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Keep supplier reminders, daily to-do checklists, and business ideas auto-saved in your
            workspace.
          </p>
        </div>
        <button
          type="button"
          onClick={handleNewNote}
          className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" />
          New Note
        </button>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12 min-h-[540px]">
        {/* Left List */}
        <div className="lg:col-span-4 flex flex-col rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
          <div className="p-3.5 border-b border-slate-100 dark:border-slate-800">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search notes..."
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-100"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
              </div>
            ) : notes.length === 0 ? (
              <div className="p-8 text-center">
                <StickyNote className="mx-auto h-8 w-8 text-slate-400" />
                <p className="mt-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  No notes yet
                </p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Click &ldquo;New Note&rdquo; to start writing.
                </p>
              </div>
            ) : (
              notes.map((n) => {
                const isActive = n.id === selectedId;
                const doneCount = (n.checklist || []).filter((t) => t.done).length;
                const totalTasks = (n.checklist || []).length;
                return (
                  <button
                    key={n.id}
                    type="button"
                    onClick={() => selectNoteObject(n)}
                    className={`w-full text-left p-4 transition-colors ${
                      isActive
                        ? "bg-brand-50/70 dark:bg-brand-950/40 border-l-2 border-brand-600"
                        : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-display text-sm font-bold text-slate-900 dark:text-white truncate">
                        {n.title || "Untitled Note"}
                      </span>
                      {n.is_pinned && <Pin className="h-3.5 w-3.5 shrink-0 text-amber-500" />}
                    </div>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                      {n.content || (totalTasks > 0 ? `${doneCount}/${totalTasks} tasks done` : "Empty note")}
                    </p>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                      <span className="rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-0.5 font-medium text-slate-600 dark:text-slate-300">
                        {n.category || "General"}
                      </span>
                      <span>{formatDate(n.updated_at)}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Editor */}
        <div className="lg:col-span-8 flex flex-col rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 sm:p-6">
          {!activeNote ? (
            <div className="flex flex-1 flex-col items-center justify-center text-center py-16">
              <StickyNote className="h-10 w-10 text-slate-300 dark:text-slate-700" />
              <h3 className="mt-3 font-display text-base font-bold text-slate-900 dark:text-white">
                Select or create a note
              </h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                All notes auto-save privately to your business workspace.
              </p>
            </div>
          ) : (
            <div className="flex flex-1 flex-col gap-4">
              {/* Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-2.5 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => setIsPinned((v) => !v)}
                    className={`inline-flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                      isPinned
                        ? "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-700 dark:bg-amber-950/60 dark:text-amber-300"
                        : "border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300"
                    }`}
                  >
                    <Pin className="h-3.5 w-3.5" />
                    {isPinned ? "Pinned" : "Pin"}
                  </button>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    {saveState === "saving" && (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin" /> Saving...
                      </>
                    )}
                    {saveState === "saved" && (
                      <>
                        <Check className="h-3 w-3 text-emerald-500" /> Saved
                      </>
                    )}
                  </span>
                  <button
                    type="button"
                    onClick={handleDelete}
                    className="rounded-lg p-1.5 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                    title="Delete note"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Title */}
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Note title..."
                className="w-full bg-transparent font-display text-xl font-extrabold text-slate-900 dark:text-white focus:outline-none"
              />

              {/* Freeform Body */}
              <textarea
                rows={7}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write meeting notes, supplier terms, pricing ideas, or reminders..."
                className="w-full flex-1 resize-none rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/60 p-3.5 text-sm text-slate-800 dark:text-slate-200 focus:border-brand-500 focus:outline-none"
              />

              {/* Interactive Checklist */}
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40 p-4">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2.5">
                  Action Checklist ({checklist.filter((t) => t.done).length}/{checklist.length})
                </p>
                <div className="space-y-2">
                  {checklist.map((item) => (
                    <div key={item.id} className="flex items-center justify-between gap-2 group">
                      <button
                        type="button"
                        onClick={() => toggleTask(item.id)}
                        className="flex items-center gap-2 text-left text-sm text-slate-800 dark:text-slate-200"
                      >
                        {item.done ? (
                          <CheckSquare className="h-4 w-4 text-brand-600 dark:text-brand-400 shrink-0" />
                        ) : (
                          <Square className="h-4 w-4 text-slate-400 shrink-0" />
                        )}
                        <span className={item.done ? "line-through text-slate-400" : ""}>
                          {item.text}
                        </span>
                      </button>
                      <button
                        type="button"
                        onClick={() => removeTask(item.id)}
                        className="opacity-0 group-hover:opacity-100 rounded p-1 text-slate-400 hover:text-rose-500"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
                <form onSubmit={addChecklistItem} className="mt-3 flex gap-2">
                  <input
                    type="text"
                    value={newTaskText}
                    onChange={(e) => setNewTaskText(e.target.value)}
                    placeholder="Add a to-do item..."
                    className="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100"
                  />
                  <button
                    type="submit"
                    className="rounded-lg bg-slate-900 dark:bg-slate-100 px-3 py-1.5 text-xs font-semibold text-white dark:text-slate-900"
                  >
                    Add
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

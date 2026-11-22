const ISO_DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;
const MS_PER_DAY = 24 * 60 * 60 * 1000;

const DATE_FORMATTER = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

/** Parses a YYYY-MM-DD string into numeric parts, or null when it is not one. */
function parseIsoParts(iso) {
  if (typeof iso !== "string") return null;
  const match = ISO_DATE_PATTERN.exec(iso.trim());
  if (!match) return null;
  return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) };
}

/** Returns the local calendar date as YYYY-MM-DD. */
export function todayIso() {
  const now = new Date();
  const year = String(now.getFullYear()).padStart(4, "0");
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Formats YYYY-MM-DD as "12 Mar 2026". Returns "—" for empty or invalid input. */
export function formatDate(iso) {
  const parts = parseIsoParts(iso);
  if (!parts) return "—";
  const date = new Date(parts.year, parts.month - 1, parts.day);
  return DATE_FORMATTER.format(date);
}

/** Whole days from fromIso to toIso (negative if toIso is earlier). NaN if either is invalid. */
export function daysBetween(fromIso, toIso) {
  const from = parseIsoParts(fromIso);
  const to = parseIsoParts(toIso);
  if (!from || !to) return NaN;
  const fromMs = Date.UTC(from.year, from.month - 1, from.day);
  const toMs = Date.UTC(to.year, to.month - 1, to.day);
  return Math.round((toMs - fromMs) / MS_PER_DAY);
}

/** True when both are valid YYYY-MM-DD strings and a is strictly earlier than b. */
export function isBeforeIso(a, b) {
  if (!parseIsoParts(a) || !parseIsoParts(b)) return false;
  return a.trim() < b.trim();
}

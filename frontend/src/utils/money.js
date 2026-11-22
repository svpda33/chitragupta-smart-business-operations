const RUPEE_PATTERN = /^\d+(\.\d{1,2})?$/;
const INVALID_AMOUNT_MESSAGE = "Enter an amount in rupees, for example 1500 or 1500.50.";
const MAX_PAISE = 1000000000;

/**
 * Converts a rupee string such as "1234.5" into integer paise (123450).
 * Throws when the string is not a plain non-negative amount with at most two decimals.
 */
export function rupeeStringToPaise(value) {
  if (typeof value !== "string") {
    throw new Error(INVALID_AMOUNT_MESSAGE);
  }
  const trimmed = value.trim();
  if (!RUPEE_PATTERN.test(trimmed)) {
    throw new Error(INVALID_AMOUNT_MESSAGE);
  }

  const [wholePart, fractionPart] = trimmed.split(".");
  const decimals = (fractionPart ?? "").padEnd(2, "0");
  return Number(wholePart) * 100 + Number(decimals);
}

/**
 * Returns null when the rupee input is valid, otherwise the error text to show.
 */
export function validateRupeeInput(value, { allowZero = false } = {}) {
  const trimmed = typeof value === "string" ? value.trim() : "";
  if (trimmed === "") {
    return "This field is required.";
  }

  let paise;
  try {
    paise = rupeeStringToPaise(trimmed);
  } catch {
    return INVALID_AMOUNT_MESSAGE;
  }

  if (paise === 0 && !allowZero) {
    return "Amount must be greater than zero.";
  }
  if (paise > MAX_PAISE) {
    return "Amount is too large.";
  }
  return null;
}

/**
 * Formats integer paise as a plain rupee string with two decimals, no symbol or grouping.
 * paiseToRupeeInput(150050) -> "1500.50"
 */
export function paiseToRupeeInput(paise) {
  if (!Number.isInteger(paise) || paise < 0) {
    throw new TypeError("paiseToRupeeInput expects a non-negative integer number of paise.");
  }
  const rupees = Math.floor(paise / 100);
  const remainder = paise % 100;
  return `${rupees}.${String(remainder).padStart(2, "0")}`;
}

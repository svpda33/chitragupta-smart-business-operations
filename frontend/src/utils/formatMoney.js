/**
 * Formats an integer amount in paise as an Indian-rupee string with two decimals.
 * Indian grouping: last three digits, then groups of two.
 *
 * formatPaiseToRupees(123456) -> "₹1,234.56"
 * formatPaiseToRupees(0)      -> "₹0.00"
 * formatPaiseToRupees(-5)     -> "-₹0.05"
 */
export function formatPaiseToRupees(paise) {
  if (typeof paise !== "number" || !Number.isInteger(paise)) {
    throw new TypeError("formatPaiseToRupees expects an integer number of paise.");
  }

  const sign = paise < 0 ? "-" : "";
  const absolute = Math.abs(paise);
  const rupees = Math.floor(absolute / 100);
  const remainder = absolute % 100;

  const digits = String(rupees);
  let grouped;
  if (digits.length <= 3) {
    grouped = digits;
  } else {
    const lastThree = digits.slice(-3);
    const head = digits.slice(0, -3);
    grouped = `${head.replace(/\B(?=(\d{2})+(?!\d))/g, ",")},${lastThree}`;
  }

  return `${sign}₹${grouped}.${String(remainder).padStart(2, "0")}`;
}

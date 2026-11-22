import { describe, it, expect } from "vitest";
import {
  rupeeStringToPaise,
  paiseToRupeeInput,
  validateRupeeInput,
} from "../../frontend/src/utils/money.js";
import { formatPaiseToRupees } from "../../frontend/src/utils/formatMoney.js";

describe("rupeeStringToPaise", () => {
  it("converts rupee strings to integer paise", () => {
    expect(rupeeStringToPaise("1234.5")).toBe(123450);
    expect(rupeeStringToPaise("12.34")).toBe(1234);
    expect(rupeeStringToPaise("1500")).toBe(150000);
  });

  it("trims surrounding whitespace", () => {
    expect(rupeeStringToPaise("  99.9 ")).toBe(9990);
  });

  it("throws for malformed input", () => {
    expect(() => rupeeStringToPaise("1.234")).toThrow();
    expect(() => rupeeStringToPaise("-1")).toThrow();
    expect(() => rupeeStringToPaise("abc")).toThrow();
    expect(() => rupeeStringToPaise("")).toThrow();
  });
});

describe("validateRupeeInput", () => {
  it("returns a message for zero when zero is not allowed", () => {
    expect(typeof validateRupeeInput("0")).toBe("string");
    expect(validateRupeeInput("0")).toBe("Amount must be greater than zero.");
  });

  it("accepts zero when allowZero is set", () => {
    expect(validateRupeeInput("0", { allowZero: true })).toBeNull();
  });

  it("requires a value", () => {
    expect(validateRupeeInput("   ")).toBe("This field is required.");
  });

  it("rejects invalid format and oversized amounts", () => {
    expect(validateRupeeInput("1.234")).toBe(
      "Enter an amount in rupees, for example 1500 or 1500.50."
    );
    expect(validateRupeeInput("10000001")).toBe("Amount is too large.");
  });

  it("returns null for a valid amount", () => {
    expect(validateRupeeInput("1500.50")).toBeNull();
  });
});

describe("paiseToRupeeInput", () => {
  it("formats paise as a plain rupee string", () => {
    expect(paiseToRupeeInput(150050)).toBe("1500.50");
    expect(paiseToRupeeInput(5)).toBe("0.05");
    expect(paiseToRupeeInput(0)).toBe("0.00");
  });
});

describe("formatPaiseToRupees", () => {
  it("formats with Indian grouping and a rupee symbol", () => {
    expect(formatPaiseToRupees(123456)).toBe("₹1,234.56");
    expect(formatPaiseToRupees(0)).toBe("₹0.00");
  });
});

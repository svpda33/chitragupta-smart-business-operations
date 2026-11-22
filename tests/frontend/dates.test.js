import { describe, it, expect } from "vitest";
import {
  daysBetween,
  formatDate,
  isBeforeIso,
  todayIso,
} from "../../frontend/src/utils/dates.js";

describe("daysBetween", () => {
  it("counts whole days using calendar dates", () => {
    expect(daysBetween("2026-03-01", "2026-03-15")).toBe(14);
  });

  it("is negative when the end date is earlier", () => {
    expect(daysBetween("2026-03-15", "2026-03-01")).toBe(-14);
  });

  it("handles month and year boundaries", () => {
    expect(daysBetween("2025-12-31", "2026-01-01")).toBe(1);
  });
});

describe("isBeforeIso", () => {
  it("compares valid ISO dates", () => {
    expect(isBeforeIso("2026-03-01", "2026-03-02")).toBe(true);
    expect(isBeforeIso("2026-03-02", "2026-03-01")).toBe(false);
    expect(isBeforeIso("2026-03-01", "2026-03-01")).toBe(false);
  });

  it("returns false for invalid input", () => {
    expect(isBeforeIso("", "2026-03-01")).toBe(false);
  });
});

describe("formatDate", () => {
  it("formats an ISO date for display", () => {
    expect(formatDate("2026-03-12")).toBe("12 Mar 2026");
  });

  it("returns an em dash for empty input", () => {
    expect(formatDate("")).toBe("—");
  });
});

describe("todayIso", () => {
  it("returns a YYYY-MM-DD string", () => {
    expect(todayIso()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

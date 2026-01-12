import { describe, it, expect } from "vitest";
import { formatDate, formatFileSize, formatDateRange } from "./format";

describe("formatDate", () => {
  it("should return 'Unknown' for undefined input", () => {
    expect(formatDate(undefined)).toBe("Unknown");
  });

  it("should return 'Unknown' for empty string", () => {
    expect(formatDate("")).toBe("Unknown");
  });

  it("should format a valid date string", () => {
    const result = formatDate("2024-01-15T14:30:00");
    expect(result).toContain("2024");
    expect(result).toContain("Jan");
  });

  it("should format date with short style (no time)", () => {
    const result = formatDate("2024-01-15T14:30:00", { style: "short" });
    expect(result).toContain("2024");
    expect(result).toContain("Jan");
    expect(result).not.toContain(":");
  });

  it("should handle date with Z suffix", () => {
    const result = formatDate("2024-01-15T14:30:00Z");
    expect(result).toContain("2024");
  });

  it("should apply EXIF offset", () => {
    const result = formatDate("2024-01-15T14:30:00", {
      exifOffset: "+05:00",
    });
    expect(result).toContain("2024");
  });

  it("should return 'Invalid Date' for invalid date string", () => {
    expect(formatDate("not-a-date")).toBe("Invalid Date");
  });
});

describe("formatFileSize", () => {
  it("should return 'Unknown' for undefined input", () => {
    expect(formatFileSize(undefined)).toBe("Unknown");
  });

  it("should return 'Unknown' for 0 bytes", () => {
    expect(formatFileSize(0)).toBe("Unknown");
  });

  it("should format bytes", () => {
    expect(formatFileSize(500)).toBe("500 B");
  });

  it("should format kilobytes", () => {
    expect(formatFileSize(1536)).toBe("1.5 KB");
  });

  it("should format megabytes", () => {
    expect(formatFileSize(1572864)).toBe("1.5 MB");
  });

  it("should format large files", () => {
    expect(formatFileSize(10485760)).toBe("10.0 MB");
  });
});

describe("formatDateRange", () => {
  it("should return single year for same year range", () => {
    const result = formatDateRange("2024-01-01T00:00:00Z", "2024-12-31T00:00:00Z");
    expect(result).toBe("Photos from 2024");
  });

  it("should return year range for multi-year range", () => {
    const result = formatDateRange("2020-01-01T00:00:00Z", "2024-12-31T00:00:00Z");
    expect(result).toBe("2020 - 2024");
  });

  it("should handle dates without Z suffix", () => {
    const result = formatDateRange("2024-01-01T00:00:00", "2024-12-31T00:00:00");
    expect(result).toBe("Photos from 2024");
  });

  it("should handle invalid dates gracefully", () => {
    const result = formatDateRange("invalid-date", "2024-12-31T00:00:00");
    expect(result).toBe("Invalid date range");
  });
});

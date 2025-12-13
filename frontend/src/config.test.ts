import { describe, it, expect } from "vitest";
import { S3_BASE_URL } from "./config";

describe("config", () => {
  it("should have S3_BASE_URL defined", () => {
    expect(S3_BASE_URL).toBeDefined();
    expect(typeof S3_BASE_URL).toBe("string");
  });

  it("should have a valid S3_BASE_URL format", () => {
    expect(S3_BASE_URL).toMatch(/^https?:\/\//);
  });
});

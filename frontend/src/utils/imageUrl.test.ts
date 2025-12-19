/**
 * Tests for image URL utility functions
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { buildS3Url, getDetailImageUrl } from "./imageUrl";
import type { Photo } from "../types/api";

// Mock the config module
vi.mock("../config", () => ({
  S3_BASE_URL: "https://test-s3.example.com",
}));

describe("buildS3Url", () => {
  it("should return null for undefined path", () => {
    expect(buildS3Url(undefined)).toBeNull();
  });

  it("should return full URL as-is if it starts with http://", () => {
    const url = "http://example.com/image.jpg";
    expect(buildS3Url(url)).toBe(url);
  });

  it("should return full URL as-is if it starts with https://", () => {
    const url = "https://example.com/image.jpg";
    expect(buildS3Url(url)).toBe(url);
  });

  it("should construct URL with base domain for relative path", () => {
    const path = "photos/image.jpg";
    expect(buildS3Url(path)).toBe("https://test-s3.example.com/photos/image.jpg");
  });

  it("should handle path with leading slash", () => {
    const path = "/photos/image.jpg";
    expect(buildS3Url(path)).toBe("https://test-s3.example.com/photos/image.jpg");
  });
});

describe("getDetailImageUrl", () => {
  const createMockPhoto = (overrides?: Partial<Photo>): Photo => ({
    uuid: "test-uuid",
    original_filename: "test.jpg",
    date: "2024-01-01",
    ...overrides,
  });

  it("should return empty string for null photo", () => {
    expect(getDetailImageUrl(null)).toBe("");
  });

  it("should prioritize s3_key_path (medium) over other paths", () => {
    const photo = createMockPhoto({
      s3_key_path: "medium/image.jpg",
      s3_original_path: "original/image.jpg",
      s3_edited_path: "edited/image.jpg",
      s3_thumbnail_path: "thumb/image.jpg",
    });
    expect(getDetailImageUrl(photo)).toBe("https://test-s3.example.com/medium/image.jpg");
  });

  it("should use s3_original_path if s3_key_path is not available", () => {
    const photo = createMockPhoto({
      s3_original_path: "original/image.jpg",
      s3_edited_path: "edited/image.jpg",
      s3_thumbnail_path: "thumb/image.jpg",
    });
    expect(getDetailImageUrl(photo)).toBe("https://test-s3.example.com/original/image.jpg");
  });

  it("should use s3_edited_path if medium and original are not available", () => {
    const photo = createMockPhoto({
      s3_edited_path: "edited/image.jpg",
      s3_thumbnail_path: "thumb/image.jpg",
    });
    expect(getDetailImageUrl(photo)).toBe("https://test-s3.example.com/edited/image.jpg");
  });

  it("should use s3_thumbnail_path if no higher resolution is available", () => {
    const photo = createMockPhoto({
      s3_thumbnail_path: "thumb/image.jpg",
    });
    expect(getDetailImageUrl(photo)).toBe("https://test-s3.example.com/thumb/image.jpg");
  });

  it("should fallback to url property if no S3 paths are available", () => {
    const photo = createMockPhoto({
      url: "https://other-cdn.example.com/image.jpg",
    });
    expect(getDetailImageUrl(photo)).toBe("https://other-cdn.example.com/image.jpg");
  });

  it("should return empty string if no URL is available", () => {
    const photo = createMockPhoto({});
    expect(getDetailImageUrl(photo)).toBe("");
  });

  it("should handle absolute URLs in S3 paths", () => {
    const photo = createMockPhoto({
      s3_key_path: "https://direct-s3.example.com/image.jpg",
    });
    expect(getDetailImageUrl(photo)).toBe("https://direct-s3.example.com/image.jpg");
  });
});

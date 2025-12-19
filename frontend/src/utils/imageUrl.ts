/**
 * Utility functions for building image URLs
 */

import type { Photo } from "../types/api";
import { S3_BASE_URL } from "../config";

/**
 * Build an S3 URL from a path
 * @param s3Path - The S3 path (can be relative or absolute URL)
 * @returns The full URL or null if path is undefined
 */
export const buildS3Url = (s3Path: string | undefined): string | null => {
  if (!s3Path) return null;
  // If already a full URL, return as-is
  if (s3Path.startsWith("http://") || s3Path.startsWith("https://")) {
    return s3Path;
  }
  // Otherwise, construct URL with base domain
  const cleanPath = s3Path.startsWith("/") ? s3Path.substring(1) : s3Path;
  return `${S3_BASE_URL}/${cleanPath}`;
};

/**
 * Get the detail image URL for a photo, prioritizing higher-resolution versions
 * @param photo - The photo object
 * @returns The URL for the highest quality available image
 */
export const getDetailImageUrl = (photo: Photo | null): string => {
  if (!photo) return "";

  // Prioritize medium (s3_key_path), then original, then edited, then thumbnail
  // This is different from the backend's url property which prioritizes thumbnail first
  const candidates = [
    photo.s3_key_path,
    photo.s3_original_path,
    photo.s3_edited_path,
    photo.s3_thumbnail_path,
  ];

  const url = candidates.map(buildS3Url).find(Boolean) || photo.url || "";

  return url;
};

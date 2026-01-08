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
 * Uses the versions array if available, otherwise falls back to individual S3 paths
 * @param photo - The photo object
 * @returns The URL for the highest quality available image
 */
export const getDetailImageUrl = (photo: Photo | null): string => {
  if (!photo) return "";

  // If versions array is available, use it to find the best quality image
  if (photo.versions && photo.versions.length > 0) {
    // Sort versions by size/resolution to get the largest one
    const sortedVersions = [...photo.versions].sort((a, b) => {
      const versionPriority: Record<string, number> = {
        full: 5,
        large: 4,
        medium: 4,
        original: 3,
        edited: 2,
      };
      const aPriority = versionPriority[a.version] || 1;
      const bPriority = versionPriority[b.version] || 1;
      return bPriority - aPriority;
    });

    // Use the highest quality version
    const bestVersion = sortedVersions[0];
    if (bestVersion?.s3_path) {
      const url = buildS3Url(bestVersion.s3_path);
      if (url) return url;
    }
  }

  // Fallback to individual S3 path fields
  // Prioritize medium (s3_key_path), then original, then edited, then thumbnail
  const candidates = [
    photo.s3_key_path,
    photo.s3_original_path,
    photo.s3_edited_path,
    photo.s3_thumbnail_path,
  ];

  const url = candidates.map(buildS3Url).find(Boolean) || photo.url || "";

  return url;
};

/**
 * Get the direct S3 share URL for a photo, prioritizing medium or edited versions
 * @param photo - The photo object
 * @returns The direct S3 URL for sharing, or empty string if not available
 */
export const getShareUrl = (photo: Photo | null): string => {
  if (!photo) return "";

  // Priority order: medium, edited, original
  const versionPriority: Record<string, number> = {
    full: 4,
    medium: 3,
    edited: 2,
    original: 1,
  };

  // If versions array is available, find the best share version
  if (photo.versions && photo.versions.length > 0) {
    // Sort by priority
    const sortedVersions = [...photo.versions].sort((a, b) => {
      const aPriority = versionPriority[a.version] || 0;
      const bPriority = versionPriority[b.version] || 0;
      return bPriority - aPriority;
    });

    // Use the highest priority version
    const bestVersion = sortedVersions[0];
    if (bestVersion?.s3_path) {
      const url = buildS3Url(bestVersion.s3_path);
      if (url) return url;
    }
  }

  // Fallback to individual S3 path fields
  // Prioritize edited, then original
  const candidates = [
    photo.s3_edited_path,
    photo.s3_original_path,
    photo.s3_key_path,
  ];

  const url = candidates.map(buildS3Url).find(Boolean) || "";

  return url;
};

/**
 * Shared formatting utility functions
 */

/**
 * Formats a date string for display
 * @param dateString - ISO date string (assumed to be UTC if no timezone)
 * @param options - Optional formatting options
 * @returns Formatted date string
 * 
 * @note Currently uses 'en-US' locale. Future enhancement: make locale configurable
 */
export function formatDate(
  dateString?: string,
  options?: {
    exifOffset?: string; // EXIF offset like "+05:00" or "-08:00"
    style?: "full" | "short"; // full: includes time, short: date only
  }
): string {
  if (!dateString) return "Unknown";

  // The timestamp is in UTC, so append 'Z' if not already present
  const utcDateString = dateString.endsWith("Z") ? dateString : `${dateString}Z`;
  const date = new Date(utcDateString);

  // Check if date is valid
  if (isNaN(date.getTime())) {
    return "Invalid Date";
  }

  // Apply EXIF offset if provided
  if (options?.exifOffset) {
    const match = options.exifOffset.match(/([+-])(\d{2}):(\d{2})/);
    if (match) {
      const sign = match[1] === "+" ? 1 : -1;
      const hours = parseInt(match[2], 10);
      const minutes = parseInt(match[3], 10);
      const offsetMs = sign * (hours * 60 + minutes) * 60 * 1000;

      // Apply the offset to get local time
      const localDate = new Date(date.getTime() + offsetMs);
      return localDate.toLocaleString("en-US");
    }
  }

  // Format based on style
  if (options?.style === "short") {
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  // Default: full format with time
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Formats a file size in bytes to a human-readable string
 * @param bytes - File size in bytes
 * @returns Formatted file size string (e.g., "1.5 MB")
 */
export function formatFileSize(bytes?: number): string {
  if (!bytes) return "Unknown";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

/**
 * Formats a date range, showing only years if the range spans multiple years
 * @param startDate - Start date string
 * @param endDate - End date string
 * @returns Formatted date range string
 * 
 * @note Assumes valid ISO date strings. Invalid dates may produce unexpected results.
 */
export function formatDateRange(startDate: string, endDate: string): string {
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  // Handle invalid dates gracefully
  if (isNaN(start.getTime()) || isNaN(end.getTime())) {
    return "Invalid date range";
  }
  
  const startYear = start.getFullYear();
  const endYear = end.getFullYear();

  if (startYear === endYear) {
    return `Photos from ${startYear}`;
  }
  return `${startYear} - ${endYear}`;
}

/**
 * URL query parameter utilities
 */

/**
 * Safely extracts a string value from a URL query parameter.
 * Vue Router's LocationQueryValue can be: string | null
 * And it can be an array: (string | null)[]
 * This function handles all cases and returns a clean string or empty string.
 * 
 * @param value - The query parameter value from route.query
 * @returns A string value, or empty string if the parameter is missing/null
 */
export function getStringParam(value: string | (string | null)[] | null | undefined): string {
  if (!value) return "";
  if (Array.isArray(value)) {
    const first = value[0];
    return first || "";
  }
  return value;
}

import type { Place } from "../types/api";

/**
 * Formats a place object for display, showing only top-level fields
 * and excluding nested objects like "names" and "address".
 *
 * @param place - The place object to format (can be Place, string, or other types)
 * @returns A formatted string with pipe-separated place information, or empty string
 */
export function formatPlace(place: unknown): string {
  if (!place) return "";
  if (typeof place === "string") return place;
  if (typeof place !== "object") return "";

  const placeObj = place as Place;
  const parts: string[] = [];

  // Show the main name if available
  if (placeObj.name) {
    parts.push(placeObj.name);
  }

  // Show address_str if available (more readable than nested address object)
  if (placeObj.address_str) {
    parts.push(`Address: ${placeObj.address_str}`);
  }

  // Show if it's home
  if (placeObj.ishome === true) {
    parts.push("(Home)");
  }

  // Show country code
  if (placeObj.country_code) {
    parts.push(`Country: ${placeObj.country_code}`);
  }

  return parts.join(" | ");
}

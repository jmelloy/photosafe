/**
 * Frontend configuration
 */

/**
 * S3 base URL for photo storage
 * Can be overridden via VITE_S3_BASE_URL environment variable
 */
export const S3_BASE_URL = import.meta.env.VITE_S3_BASE_URL || "https://photos.melloy.life";

/**
 * Development mode flag
 */
export const IS_DEV = import.meta.env.DEV;

/**
 * Debug logging helper - only logs in development mode
 */
export const debugLog = (...args: any[]) => {
  if (IS_DEV) {
    console.log(...args);
  }
};

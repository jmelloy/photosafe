/**
 * Shared error handling utilities
 */

/**
 * Type guard for Axios-like error responses
 */
interface AxiosLikeError {
  response?: {
    status?: number;
    data?: { detail?: string };
  };
  message?: string;
  code?: string;
}

function isAxiosLikeError(error: unknown): error is AxiosLikeError {
  return (
    typeof error === "object" &&
    error !== null &&
    ("response" in error || "message" in error || "code" in error)
  );
}

/**
 * Format an API error for display to users
 * @param error - The error object from the API call
 * @returns A user-friendly error message
 */
export function formatApiError(error: unknown): string {
  // Handle Axios-like errors
  if (isAxiosLikeError(error)) {

    // Handle specific HTTP status codes
    if (error.response?.status === 401) {
      return "Invalid username or password";
    }

    if (error.response?.status === 403) {
      return "You don't have permission to perform this action";
    }

    if (error.response?.status === 404) {
      return "The requested resource was not found";
    }

    // Handle network errors
    if (
      error.code === "ECONNREFUSED" ||
      error.message?.includes("Network Error")
    ) {
      return "Cannot connect to server. Is the backend running?";
    }

    // Return detailed error message if available
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }

    // Return generic message with error text if available
    if (error.message) {
      return `An error occurred: ${error.message}`;
    }
  }

  // Fallback for unknown error types
  return "An unexpected error occurred. Please try again.";
}

/**
 * Log an error to the console with context
 * @param context - Description of where/what was happening when the error occurred
 * @param error - The error object
 */
export function logError(context: string, error: unknown): void {
  console.error(`[${context}] Error:`, error);

  // Log additional details for Axios-like errors
  if (isAxiosLikeError(error)) {

    console.error(`[${context}] Details:`, {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
    });
  }
}

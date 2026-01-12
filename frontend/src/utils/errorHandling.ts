/**
 * Shared error handling utilities
 */

/**
 * Format an API error for display to users
 * @param error - The error object from the API call
 * @returns A user-friendly error message
 */
export function formatApiError(error: unknown): string {
  // Handle Axios-like errors
  if (typeof error === "object" && error !== null && "response" in error) {
    const axiosError = error as {
      response?: {
        status?: number;
        data?: { detail?: string };
      };
      message?: string;
      code?: string;
    };

    // Handle specific HTTP status codes
    if (axiosError.response?.status === 401) {
      return "Invalid username or password";
    }

    if (axiosError.response?.status === 403) {
      return "You don't have permission to perform this action";
    }

    if (axiosError.response?.status === 404) {
      return "The requested resource was not found";
    }

    // Handle network errors
    if (
      axiosError.code === "ECONNREFUSED" ||
      axiosError.message?.includes("Network Error")
    ) {
      return "Cannot connect to server. Is the backend running?";
    }

    // Return detailed error message if available
    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail;
    }

    // Return generic message with error text if available
    if (axiosError.message) {
      return `An error occurred: ${axiosError.message}`;
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
  if (typeof error === "object" && error !== null && "response" in error) {
    const axiosError = error as {
      response?: {
        status?: number;
        data?: unknown;
      };
      message?: string;
    };

    console.error(`[${context}] Details:`, {
      message: axiosError.message,
      status: axiosError.response?.status,
      data: axiosError.response?.data,
    });
  }
}

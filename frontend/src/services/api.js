import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 15000,
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});

/**
 * Normalises any Axios failure into a plain object:
 *   { message, fieldErrors, status }
 * - message: human-readable text (detail string, first field error, generic
 *   fallback, or a connectivity message when there is no response).
 * - fieldErrors: { [field]: message } built from body.errors[].
 * - status: HTTP status code, or null when no response was received.
 */
function normaliseError(error) {
  const response = error?.response;

  if (!response) {
    return {
      message: "Cannot reach the server. Check that the backend is running.",
      fieldErrors: {},
      status: null,
    };
  }

  const body = response.data ?? {};
  const fieldErrors = {};
  if (Array.isArray(body.errors)) {
    for (const item of body.errors) {
      if (item && typeof item.field === "string" && typeof item.message === "string") {
        fieldErrors[item.field] = item.message;
      }
    }
  }

  let message;
  if (typeof body.detail === "string" && body.detail.trim()) {
    message = body.detail;
  } else if (Object.keys(fieldErrors).length > 0) {
    message = Object.values(fieldErrors)[0];
  } else {
    message = "The server returned an error.";
  }

  return { message, fieldErrors, status: response.status ?? null };
}

api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normaliseError(error))
);

export default api;

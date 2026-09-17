// Single source for server-side env vars used by Next.js route handlers.
// The browser never reads these — they are server-only constants (ADR-0005).
export const FASTAPI_URL =
  process.env.FASTAPI_INTERNAL_URL ?? "http://localhost:8000"

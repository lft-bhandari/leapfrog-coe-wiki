# Next.js: server components for data, route handlers for streaming, proxy for FastAPI

`apps/web/` uses React Server Components (RSC) for all data fetching by default. The only exception is the chat stream, which uses a Next.js route handler (`/api/chat`) that proxies the FastAPI streaming response. The browser never calls FastAPI directly — Next.js is the single public surface.

## Pattern

| Concern | Mechanism |
|---|---|
| Graph data, wiki page reads | React Server Component fetches FastAPI internally |
| Chat stream | `app/api/chat/route.ts` proxies FastAPI stream to the browser |
| Auth enforcement | Next.js middleware (`middleware.ts`) — one place, covers all routes |
| Static/shared data | Fetched in a layout, passed as props |

## Why

- **Server components for data**: eliminates client-side loading states for non-interactive data; no `useEffect` fetch waterfalls.
- **Proxy over direct browser→FastAPI calls**: auth (Google OAuth, ticket 10) is enforced once in Next.js middleware rather than duplicated across FastAPI and the browser. The FastAPI URL never leaks to the client.
- **Route handlers only for streaming**: the chat stream is the only case that genuinely requires a browser-to-server connection; everything else is rendered server-side.

## Considered options

- **tRPC**: end-to-end type safety between Next.js and FastAPI. Rejected: FastAPI is a Python backend; TypeScript type sync is manual either way, so tRPC adds ceremony without the core benefit.
- **Route handlers for all FastAPI calls**: uniform proxy layer, but adds unnecessary latency and boilerplate for non-streaming data that server components can fetch directly.

## Consequences

Server components must not use browser APIs or React state — add `"use client"` only when the component genuinely needs interactivity. The internal FastAPI base URL is set via `FASTAPI_INTERNAL_URL` environment variable, never hardcoded.

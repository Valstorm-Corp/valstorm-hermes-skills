---
name: valstorm-react-patterns
description: Use for React performance, state bypasses, and layout.
---

# Valstorm React Patterns

Use this skill when implementing complex frontend components in the Valstorm monorepo.

## Rapid State Updates & Choppiness (e.g., Speech-to-Text, WebSockets)
When receiving rapid, continuous updates (such as partial Speech-to-Text transcripts arriving multiple times per second via a WebSocket), **DO NOT use React state (`setState` / `useState`) for the partial updates**.
- **The Pitfall:** Calling state updates rapidly triggers continuous full component re-renders. This causes input locking, UI lag, and "choppiness" when typing or rendering streaming text.
- **The Solution:** Bypass React state entirely for live partials. Mutate the DOM directly via a ref (e.g., `textareaRef.current.value = partialText`), and manually trigger any resize logic. Only sync the final payload back into React state when the stream is completed (`isFinal === true`).

## Authenticating WebSockets
When initializing a WebSocket connection (like `useAssemblyWhisper` or `useValstormWebSocket`) that connects back to the Valstorm API:
1. You must retrieve the user's token using `getUniversalTokens()` from `@monorepo/utils`.
2. Do not attempt to send the authentication payload before `ws.onopen` completes.
3. The backend requires a strict `{"type": "authenticate", "token": "..."}` JSON payload immediately upon connection. If the first message is anything else, the server drops the socket.

## Layout and Height Propagation
Inside `RecordAppPage.tsx` or similar wrapper shells, never use `h-full` or `min-h-0` on the root container. See `CLAUDE.md` under "Visual Layout & Height Propagation Contract" for full layout guardrails.
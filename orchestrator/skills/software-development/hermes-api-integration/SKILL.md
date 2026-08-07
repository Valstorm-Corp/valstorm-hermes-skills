---
name: hermes-api-integration
description: "How to natively consume the local Hermes Agent API Server via REST and SSE."
tags: [hermes, api, sse, streaming, local-llm, openai-compatible]
---

# Hermes API Integration

Hermes includes a robust, fully native OpenAI-compatible REST API Server built directly into its messaging gateway (`gateway/platforms/api_server.py`). It natively exposes standard OpenAI endpoints, allowing you to connect a Next.js backend, mobile app, or desktop client directly using the official `openai` SDK or standard HTTP fetch.

## Setup & Configuration

Enable the API server and set your credentials via the Hermes CLI:

```bash
hermes config set API_SERVER_ENABLED true
# The key must be at least 8 characters long for security
hermes config set API_SERVER_KEY "your_strong_secret_api_key_here"
hermes config set API_SERVER_HOST "127.0.0.1"
hermes config set API_SERVER_PORT 8000
```

Start the Gateway:
```bash
hermes gateway start  # Runs in background
# OR
hermes gateway run    # Runs in foreground for debugging
```

### CORS Configuration
If your frontend (like a Next.js app on `localhost:3000`) attempts to hit `127.0.0.1:8000` via a browser `fetch()`, you will encounter a CORS (`No Access-Control-Allow-Origin header`) block. 
Configure the allowed origins in Hermes to fix this natively:
```bash
hermes config set API_SERVER_CORS_ORIGINS "*"
```

## Consuming the API (Server-Sent Events)

Because it is 100% OpenAI-compliant, you can consume it natively with the `openai` JS/Python SDK, or by manually streaming the Server-Sent Events (SSE).

### Option 1: OpenAI SDK
```typescript
import { OpenAI } from "openai";

const hermes = new OpenAI({
  baseURL: "http://127.0.0.1:8000/v1",
  apiKey: "your_strong_secret_api_key_here",
});

const response = await hermes.chat.completions.create({
  model: "orchestrator", // Routes to specific profile memory!
  messages: [{ role: "user", content: "Design the billing schema" }],
  stream: true,
});

for await (const chunk of response) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

### Option 2: Raw Fetch Stream (SSE)
When writing custom React implementations (like a background Electron daemon), loop over the lines and parse `choices[0].delta.content`.

**Critical Sync Pitfall 1 (DDoS Loop):** Do NOT wait until `done === true` to process tokens if you are trying to stream to a UI or relay server. You must push chunks to your backend sync route incrementally inside the `line.startsWith("data: ")` loop. Ensure you `await` the sync fetch and check `if (!res.ok) { break; }` to prevent DDoS-ing your backend with 50 tight-loop fetch requests if the sync route throws a 500 error.

**Critical Sync Pitfall 2 (String Doubling):** When syncing SSE delta chunks incrementally to a database, be extremely careful about string concatenation logic between the frontend and backend.
*   **The Bug**: The frontend accumulates tokens locally (`currentText += content`) and sends the *full accumulated string* in the payload (`{ text: currentText }`). The backend receives it and appends it to the existing database record (`new_text = record.body + data.text`). This causes exponential doubling in the database (`Hello` -> `HelloHello World`).
*   **The Fix**: If the frontend sends the *full* accumulated string, the backend must strictly *overwrite* the database cell (`content: data.text`). If the backend appends, the frontend must only send the isolated *delta* chunk (`content`).

**Critical Sync Pitfall 3 (Amnesia & Session Tracking):** By default, OpenAI API calls are fully stateless. If you are communicating with a stateful local LLM (like Hermes) from an external UI, passing just the latest `user` message will cause the AI to forget the conversation.
*   **The Fix**: The UI must extract the `session_id` (e.g. `chatcmpl-...`) from the first returned SSE chunk (`parsed.session_id || parsed.id`). On subsequent requests to the local Hermes instance, include `session_id: "chatcmpl-..."` in the JSON request body. This allows Hermes to look up its own internal SQLite memory for the thread instead of forcing the UI to bloat the request by re-transmitting the entire message history array.

**Critical Sync Pitfall 4 (React/Jotai Streaming Integration):** When pushing raw chunks to a React/Jotai UI, developers frequently encounter duplicate execution bugs from `useEffect`, blocky UI updates from overly-fast local LLMs, and duplicated message bubbles during the backend CUD sync handoff. 
*   **Reference:** See `references/react-sse-streaming-patterns.md` for the exact implementations of the `onMessage` Websocket fix, the `TypewriterMessageRenderer` visual smoother, and the `withoutOptimistic` CUD filter.

**Critical Sync Pitfall 3 (Amnesia & Session Tracking):** By default, OpenAI API calls are fully stateless. If you are communicating with a stateful local LLM (like Hermes) from an external UI, passing just the latest `user` message will cause the AI to forget the conversation.
*   **The Fix**: The UI must extract the `session_id` (e.g. `chatcmpl-...`) from the first returned SSE chunk (`parsed.session_id || parsed.id`). On subsequent requests to the local Hermes instance, include `session_id: "chatcmpl-..."` in the JSON request body. This allows Hermes to look up its own internal SQLite memory for the thread instead of forcing the UI to bloat the request by re-transmitting the entire message history array.

**Critical Sync Pitfall 4 (React/Jotai Streaming Integration):** When pushing raw chunks to a React/Jotai UI, developers frequently encounter duplicate execution bugs from `useEffect`, blocky UI updates from overly-fast local LLMs, and duplicated message bubbles during the backend CUD sync handoff. 
*   **Reference:** See `references/react-sse-streaming-patterns.md` for the exact implementations of the `onMessage` Websocket fix, the `TypewriterMessageRenderer` visual smoother, and the `withoutOptimistic` CUD filter.

### Stateful Sessions (Memory)
Hermes maintains its own internal SQLite memory. To avoid bloating your context window by re-sending the entire message history array on every turn:
1. Extract the session ID from the first SSE chunk: `const sessionId = parsed.session_id || parsed.id;`
2. Save this `sessionId` to your database.
3. On subsequent requests, pass `session_id: sessionId` in the payload body (with only the latest user message) to seamlessly resume the thread.

```javascript
const res = await fetch("http://127.0.0.1:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${API_KEY}`
  },
  body: JSON.stringify({
    model: "orchestrator", // Routes to specific Hermes profile
    messages: [{ role: "user", content: "Hello Hermes" }],
    stream: true,
    session_id: "chatcmpl-..." // Include to resume state
  })
});

const reader = res.body?.getReader();
const decoder = new TextDecoder("utf-8");

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunkStr = decoder.decode(value, { stream: true });
  const lines = chunkStr.split("\n").filter(l => l.trim() !== "");
  
  for (const line of lines) {
    if (line.startsWith("data: ") && line !== "data: [DONE]") {
      const parsed = JSON.parse(line.slice(6));
      const content = parsed.choices?.[0]?.delta?.content;
      
      // Capture session ID on first chunk
      const sessionId = parsed.session_id || parsed.id;
      
      if (content) {
         // Push the token chunk incrementally!
         // await syncToBackend(content);
      }
    }
  }
}
```
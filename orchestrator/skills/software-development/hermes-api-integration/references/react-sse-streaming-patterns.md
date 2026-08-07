# Real-Time SSE Streaming to React/Jotai UI

When bridging an OpenAI-compatible Server-Sent Events (SSE) stream to a React frontend, several complex race conditions and visual jitter bugs can emerge. This reference captures the proven pattern for successfully parsing the stream, maintaining UI state (Jotai), and smoothly rendering the text (Typewriter Effect) without OpenSearch or database sync race conditions.

## 1. The SSE Fetch & Parse Loop

**The Pitfall:** The browser's native `fetch` reader produces chunks that do not guarantee a 1:1 mapping with JSON objects. A chunk might end mid-JSON string, causing `JSON.parse()` to throw an exception.

**The Solution:** You must buffer incoming text, split by newlines, process complete lines, and crucially, **hold back the final incomplete line** in the buffer for the next chunk read.

```typescript
// Inside an async function (e.g. executing local LLM)
let currentText = "";
const res = await fetch("http://127.0.0.1:8000/v1/chat/completions", { /* ... */ });
const reader = res.body?.getReader();
const decoder = new TextDecoder("utf-8");
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) {
     // Handle final completion state (e.g., set status: "completed")
     setStreamingChunk({ chat_id: payload.chat_id, chunk: currentText, status: "completed" });
     break;
  }
  
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n");
  
  // Keep the last partial line in the buffer (it might be incomplete JSON)
  buffer = lines.pop() || "";
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith("data: ") && !trimmedLine.includes("[DONE]")) {
      const dataPayload = trimmedLine.substring(6).trim();
      if (!dataPayload) continue;
      
      try {
        const parsed = JSON.parse(dataPayload);
        const content = parsed.choices?.[0]?.delta?.content;
        
        // Extract session_id for stateful thread tracking if present
        if (!hermesSessionId) {
           hermesSessionId = parsed.session_id || parsed.id || null;
        }

        if (content) {
          currentText += content;
          // Sync to local UI Jotai state instantly
          setStreamingChunk({ chat_id: payload.chat_id, chunk: currentText, status: "streaming" });
        }
      } catch (e) {
        console.warn("Failed to parse SSE JSON chunk:", dataPayload);
      }
    }
  }
}
```

## 2. Preventing useEffect Duplicate Executions (The React Trap)

**The Pitfall:** When processing incoming WebSocket commands (that trigger the above SSE loop), developers often use a `useEffect` hooked to a `lastMessage` variable. If the component re-renders (due to typing in an input box or routing), the `useEffect` dependencies change, and it processes the exact same `lastMessage` again, causing duplicate LLM executions.

**The Solution:** Move command parsing entirely OUT of `useEffect` and into the WebSocket's `onMessage` event callback.

```typescript
// Bad:
useEffect(() => {
  if (lastMessage) { /* executeLocalLLM() */ }
}, [lastMessage, router, access_token]); // Re-runs constantly!

// Good:
const { sendMessage, readyState } = useWebSocket(userWebsocketUrl, {
  onMessage: (event) => {
    try {
      const message = JSON.parse(event.data);
      if (message.type === "DESKTOP_COMMAND") {
         // Execute once, immune to React component re-renders
      }
    } catch (e) {}
  }
});
```

## 3. The Typewriter Renderer (Smoothing the Visuals)

**The Pitfall:** Local LLMs stream tokens significantly faster than the eye can read (e.g. 150+ chars per tick). If the UI binds directly to the incoming text state, the text will slam onto the screen in massive, jagged, unreadable bricks.

**The Solution:** Decouple the data stream from the visual stream using an internal `requestAnimationFrame` buffer component.

```tsx
const TypewriterMessageRenderer = ({ content, incoming, paper, onUpdate }) => {
  const [displayedContent, setDisplayedContent] = useState("");
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate; // Keep callback reference fresh

  useEffect(() => {
    if (!content) return;
    let animationFrameId;
    
    const updateContent = () => {
      setDisplayedContent((prev) => {
        if (prev.length < content.length) {
          // Reveal 3 characters per frame (~180 chars/sec at 60fps)
          return content.substring(0, prev.length + 3);
        }
        return prev;
      });
      animationFrameId = requestAnimationFrame(updateContent);
    };

    animationFrameId = requestAnimationFrame(updateContent);
    return () => cancelAnimationFrame(animationFrameId);
  }, [content]);

  // Optional auto-scroll trigger
  useEffect(() => {
    if (onUpdateRef.current) onUpdateRef.current();
  }, [displayedContent]);

  return <MessageRenderer data={{ body: displayedContent }} incoming={incoming} paper={paper} />;
};
```

## 4. The CUD Handoff (Preventing Duplicates)

**The Pitfall:** When the stream completes, the backend saves the record to the DB and fires a real-time CUD (Create/Update/Delete) WebSocket event to all clients. If the UI leaves its temporary "streaming bubble" on the screen, the user will briefly see duplicate messages side-by-side.

**The Solution:** Aggressively purge placeholder bubbles (`temp_` and `optimistic_`) in the exact moment the authoritative DB records are merged into state. Do NOT use `setTimeout` or `setInterval` to manually poll the database (e.g., `fetchMessages()`) to bypass OpenSearch cache delays. CUD WebSocket events automatically populate `recordsState` globally, making manual polling an anti-pattern. If you must fetch manually via `useApiHook`, ensure you pass `bypass_cache: true`.

```typescript
// Inside the global CUD record listener useEffect
setMessages((prev) => {
  const existingIds = new Set(prev.map((m) => m.id));
  const added = newMsgs.filter((m) => !existingIds.has(m.id));
  if (added.length === 0) return prev;
  
  // Purge optimistic and temp messages when authoritative DB records arrive
  const withoutOptimistic = prev.filter(m => {
      if (m.id && typeof m.id === 'string' && (m.id.startsWith('temp_') || m.id.startsWith('optimistic_'))) {
          return false; // Remove placeholder
      }
      return true; // Keep real records
  });

  return uniqueAndSorted([...withoutOptimistic, ...added]);
});
```
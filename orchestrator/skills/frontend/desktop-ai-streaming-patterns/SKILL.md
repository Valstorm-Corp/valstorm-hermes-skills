---
name: desktop-ai-streaming-patterns
description: Use when building desktop AI chat and streaming runs.
tags: [electron, ai-chat, streaming, hermes, sse, runs, file-tree, marquee-selection]
---

# Desktop AI Streaming & Navigation UI Patterns

Guidelines and battle-tested patterns for building real-time desktop AI chat interfaces with local agent runtimes (like Hermes), optimistic state deduplication, and high-density file tree navigations.

## 1. Hermes `/v1/runs` Two-Step SSE Lifecycle

When integrating an Electron desktop client with the local Hermes API gateway on port `8642`:

### Step 1: Initiate Run (`POST /v1/runs`)
- **Payload Schema**: Requires `input` (string), `model` (e.g. `orchestrator`), and optional `session_id` and `instructions`.
  ```json
  {
    "input": "Run df -h to check disk space",
    "model": "orchestrator",
    "session_id": "aich_123"
  }
  ```
  *(Note: Sending standard OpenAI `{ "messages": [...] }` will trigger `HTTP 400: Missing 'input' field`)*.
- **Response**: Returns `{"run_id": "run_...", "status": "started"}` with status code `202 Accepted`.

### Step 2: Stream Events (`GET /v1/runs/{run_id}/events`)
- Connect an HTTP/SSE reader with `Authorization: Bearer <gateway_key>`.
- Stream structured event types:
  - `message.delta`: Text token deltas (`delta: string`).
  - `reasoning.available`: Thinking / reasoning deltas (`text: string`).
  - `tool.started`: Tool execution starts (`tool: string`, `preview: string`).
  - `tool.completed`: Tool execution finishes (`tool: string`, `duration: number`, `error: boolean`).
  - `run.completed`: Full finalized output (`output: string`, `usage: object`).

---

## 2. React Streaming & Deduplication Pitfalls

### Pitfall 1: Role Mismatch & Double Message Bubbles
- **The Bug**: During streaming, the client creates a temporary optimistic bubble (`optimistic_<timestamp>`). When the turn finishes and syncs to MongoDB via `/desktop-sync`, the backend stores `role: "assistant"`. A WebSocket CUD listener filtering only for `m.role === "model"` fails to match, leaving the optimistic bubble in state and rendering duplicate messages.
- **The Fix**: Normalize AI roles across the client:
  ```typescript
  const isAiRole = (role: string) =>
    ["assistant", "model", "ai", "tool", "tool_result"].includes(role);

  const hasNewAiMsg = added.some((m) => isAiRole(m.role));
  ```
  When `hasNewAiMsg` is true, atomically purge all `optimistic_*` and `temp_*` entries.

### Pitfall 2: JavaScript Array Truthiness & Empty Tool Calls
- **The Bug**: `Boolean([]) === true` in JavaScript. If a completed turn has no tool calls and sends `tool_calls: []`, checking `if (msg.tool_calls)` evaluates to `true`, wiping conversational text and rendering a blank "Tool Request" bubble.
- **The Fix**: Always check array length:
  ```typescript
  const hasToolCalls = Array.isArray(msg.tool_calls)
    ? msg.tool_calls.length > 0
    : Boolean(msg.tool_calls && typeof msg.tool_calls === "object" && Object.keys(msg.tool_calls).length > 0);
  ```
  And set empty tool fields to `null` before database persistence.

### Pitfall 3: Premature Tool State Clearing
- **The Bug**: Clearing `liveToolExecutions` immediately upon `status: "completed"` causes live terminal boxes to disappear before the authoritative database record arrives, resulting in visible UI flicker.
- **The Fix**: Keep `liveToolExecutions` visible throughout the streaming container until the authoritative WebSocket CUD record lands, then clear the live state.

---

## 3. High-Density File Tree & Selection Patterns

### Rubber-Band / Marquee Drag-to-Select & Separation of Duties
- To completely eliminate interaction conflicts between single-click folder toggling, file selection, and native item dragging, **restrict marquee selection to requiring a modifier key** (`Shift`, `Cmd` / `Ctrl`, or `Option` / `Alt` + `Drag`).
- If no modifier key is held, `handlePointerDown` yields immediately, allowing native clicks and folder accordion expansion to operate with 100% reliability.
- When dragging with a modifier key held, compute bounding-box intersection against all `[data-tree-node="true"]` elements in real-time and render the marquee overlay (`bg-blue-500/15 border border-blue-500/50`).

### Preventing Double-Toggle on `Cmd+Click`
- If a child tree component (`CloudVaultTree`) delegates selection to a parent (`FileTree`) via `onRowClick`, return early in the child handler. Executing selection toggles in both child and parent cancels out the `Cmd+Click` toggle immediately.

### Reliable Folder Accordion Expansion & Directory Schema Recognition
- In async recursive trees, avoid reading `expandedPaths` from closure state.
- Always use functional state updaters (`setExpandedPaths((prev) => ...)`), synchronize `expandedPathsRef.current`, and normalize path lookups across raw IDs and `cloud://` prefixes.
- **Database Schema Inference**: Raw MongoDB records (e.g. from `SELECT * FROM vault`) often lack an explicit `isDirectory: true` column. Detect folders comprehensively:
  ```typescript
  const isFolder =
    f.isDirectory === true ||
    f.type === "directory" ||
    f.type === "folder" ||
    String(f.id || "").startsWith("vaul_") ||
    !f.name?.includes(".");
  ```
- **Eager Parent-Child Cache Linking**: Build parent-child relationships (`childrenMap.get(parent_vault || "root")`) immediately on initial mount so all nested subfolders and files in `directoryCache` expand instantly on single click with zero network lag.

### Preventing Maximum Call Stack Errors in "Expand All"
- Recursive tree walkers traversing cached directories will cause `RangeError: Maximum call stack size exceeded` on deep or circular directory trees if they lack a `visited` set.
- Maintain a local `visited: Set<string>` and iterate over `directoryCache.keys()` directly rather than re-invoking recursive walkers over `.entries()`:
  ```typescript
  const visited = new Set<string>();
  const collectKnownFolders = (nodes: any[]) => {
    if (!Array.isArray(nodes)) return;
    for (const n of nodes) {
      const cleanId = String(n.id || n.path || "").replace("cloud://", "");
      if (!cleanId || visited.has(cleanId)) continue;
      visited.add(cleanId);

      if (n.isDirectory || cleanId.startsWith("vaul_")) {
        optimisticSet.add(cleanId);
        optimisticSet.add(`cloud://${cleanId}`);
        const cached = directoryCache.get(cleanId) || directoryCache.get(`cloud://${cleanId}`);
        if (cached) collectKnownFolders(cached);
      }
    }
  };
  ```

### Real-Time Tree Filter with Ancestor Auto-Expansion
- A fast keystroke-based UI filter should match files directly and match folders if their name or any descendant in `directoryCache` matches the query.
- When a search query is active, auto-expand any folder with matching descendants (`isExpanded = Boolean(query && hasMatchingChildren) || isExpanded`) so matches are surfaced without manual expanding.

### Multi-Item Clipboard Operations
- When copying paths for multi-selections (`Cmd + C` or Context Menu), format paths newline-separated (`\n`) and reflect the selection count in context menus (`Copy Paths (${selectedPaths.size})`, `Delete (${selectedPaths.size})`).

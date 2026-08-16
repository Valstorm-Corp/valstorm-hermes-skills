# VFS UI & Hermes `/v1/runs` Integration Reference

## 1. Hermes Runs 2-Step Streaming Flow
1. **Initiate (`POST /v1/runs`)**:
   - Must send `{ "input": "...", "model": "orchestrator", "session_id": "..." }`.
   - Never send `{ "messages": [...] }` (causes 400 Bad Request: Missing 'input' field).
   - Returns `HTTP 202 Accepted` with `run_id`.
2. **Stream (`GET /v1/runs/{run_id}/events`)**:
   - Stream events: `message.delta`, `reasoning.available`, `tool.started`, `tool.completed`, `run.completed`.
   - Forward `reasoning.available` so thoughts appear live in the UI.

## 2. Optimistic UI Deduplication
- Normalize assistant roles (`["assistant", "model", "ai", "tool", "tool_result"]`).
- Keep live streaming block active until the authoritative database record arrives via WebSocket CUD.
- Guard against JS array truthiness (`Boolean([]) === true`): always check `msg.tool_calls.length > 0` before treating a message as a tool request.

## 3. High-Density File Tree & Navigation Patterns
- **Modifier-Only Marquee Selection**: Require modifier key (`Shift`/`Cmd`/`Option` + Drag) for marquee rubber-band selection to avoid any collision with single-click folder expansion, file opening, or native item drag-and-drop.
- **Directory Detection**: Detect directories by checking `f.isDirectory || f.type === "directory" || f.type === "folder" || String(f.id).startsWith("vaul_") || !f.name.includes(".")`.
- **Eager Linking**: Link parent-child nodes in memory (`directoryCache`) on mount so expansion is instant with zero network lag.
- **Stack Overflow Prevention in "Expand All"**: Use a `visited: Set<string>` inside recursive directory collectors and iterate `directoryCache.keys()` directly to prevent `RangeError: Maximum call stack size exceeded`.
- **Live Filtering**: Keystroke-based search matches files and auto-expands any folder with matching descendants (`isExpanded = Boolean(query && hasMatchingChildren) || isExpanded`).
- **Multi-Item Clipboard**: Copy paths as newline-separated strings (`\n`) and reflect selection counts on context menu actions (`Copy Paths (N)`).

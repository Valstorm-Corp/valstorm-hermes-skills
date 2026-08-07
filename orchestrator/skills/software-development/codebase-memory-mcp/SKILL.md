---
name: codebase-memory-mcp
description: "Use when querying or indexing with codebase-memory-mcp."
trigger: "When the user asks about codebase indexing, or when using cbm MCP tools like trace_path or search_graph."
---

# Codebase Memory MCP (cbm)

`codebase-memory-mcp` provides structural codebase intelligence to AI agents via MCP tools. 

## Indexing Lifecycle & Maintenance
- **Background Watcher:** The tool relies on a background watcher that incrementally updates the local knowledge graph as files are changed.
- **Manual Re-indexing:** Because of the watcher, manual full re-indexing is **rarely needed**. 
- **When to manually index:**
  1. Switching to a branch with a massively different architecture.
  2. Executing a massive `git pull` that introduces thousands of lines of changes all at once.
  3. The structural tools (e.g., `trace_path`, `search_graph`) start hallucinating, missing new files, or returning stale data.
- **How to manually index:** Use the `index_repository` MCP tool, or run `codebase-memory-mcp cli index` in the terminal.

## Agent Usage Strategy
- Prefer `cbm` MCP tools (`trace_path`, `get_architecture`, `search_graph`) over standard `grep`/`find`/`cat` loops for deep codebase exploration.
- It leverages a Hybrid LSP, enabling cross-language tracing (e.g., following a React hook directly to a FastAPI backend route).
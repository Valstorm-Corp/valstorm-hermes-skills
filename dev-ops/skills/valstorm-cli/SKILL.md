---
name: valstorm-cli
description: Use when using the Valstorm CLI to sync, query, search, ask, or deploy.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [valstorm, cli, vfs, search, rag, metadata, query]
---

# Valstorm CLI

The `valstorm` CLI is the primary tool for interacting with Valstorm workspaces, syncing metadata (push/pull), querying data, performing hybrid vector/semantic search, asking grounded RAG questions, managing developer sandboxes, and scaffolding local files. It is heavily optimized for AI workflows.

## Execution Context
Inside the Valstorm monorepo, execute the CLI via `uv` to ensure the correct environment:
`uv run --project cli valstorm <command>`

## Core Workflows for AI Agents

### 1. Data Querying (SQL & GraphQL)
The CLI includes a powerful query engine. **Always use `-o json` when reading data as an AI.**
- `uv run --project cli valstorm sql "SELECT * FROM contact LIMIT 5" -o json`
- **Special keywords**: `ME` (current user), `PHONE:` (phone search), dynamic dates (`today`, `last_n_days:7`).
- **Save to file**: Add `--save results.json` or `--csv output.csv`.

### 2. Hybrid Semantic & Metadata Search (`search` / `vfs search`)
Search files, structured metadata, and document vector chunks across the entire workspace using FastEmbed embeddings and Qdrant vector storage with Reciprocal Rank Fusion (RRF).
- `uv run --project cli valstorm search "enterprise pricing contract" --json`
- `uv run --project cli valstorm vfs search "quarterly report" -v <vault_id> -t pdf --json`
- **Flags**:
  - `--semantic-only`: Filter strictly by semantic vector similarity.
  - `--exact-only`: Filter strictly by exact metadata match.
  - `-v, --vault <id|path>`: Scope search to a specific Vault or folder path.
  - `-t, --type <ext>`: Filter by file extension (e.g. `pdf`, `md`, `docx`, `json`, `csv`, `txt`).
  - `--min-score <0.0-1.0>`: Filter matches below similarity score threshold.
  - `--plain, -p`: Output plain tab-separated (TSV) stream (`score \t match_type \t id \t location \t name`) for Unix pipelines (`fzf`, `awk`).
  - `--json`: Output raw JSON data.

### 3. Conversational Document QA (`ask` / `vfs ask`)
Ask natural language questions answered and cited by workspace documents via Server-Sent Events (SSE) streaming and grounded context.
- `uv run --project cli valstorm ask "What is the data retention policy?" --json`
- `uv run --project cli valstorm vfs ask "Summarize the master services agreement" --vault <vault_id> --raw`
- **Flags**:
  - `-v, --vault <id>`: Limit retrieval context to a specific Vault.
  - `-l, --limit <n>`: Number of document context chunks for grounding (default: 5).
  - `--no-citations`: Suppress grounded source document citations table.
  - `--raw`: Stream raw text tokens directly without Rich markup.
  - `--json`: Non-streaming JSON answer with citation sources and match scores.

### 4. Workspace Syncing (Pull & Push)
Valstorm metadata (functions, triggers, schemas, UI pages) is synced between the cloud and local filesystem.
- **Init**: `uv run --project cli valstorm init <dir>` (creates `valstorm.json`, `.mcp.json`, etc.)
- **Pull Metadata**: `uv run --project cli valstorm pull metadata`
- **Pull Schemas**: `uv run --project cli valstorm pull schemas`
- **Push Metadata**: `uv run --project cli valstorm push metadata` (pushes all changes in `object/`)
- **Push Specific**: `uv run --project cli valstorm push metadata <object_type> <file_name.py>`
- **Push Web Docs**: `uv run --project cli valstorm push web`

### 5. App & Manifest Deployment
The CLI can intelligently bundle and deploy Valstorm apps or diff-based manifests.
- **Diff Manifest**: `uv run --project cli valstorm manifest diff` (builds manifest from local git changes)
- **Deploy Manifest**: `uv run --project cli valstorm deploy manifest manifests/diff_deployment.json`
- **Deploy Local App**: `uv run --project cli valstorm deploy app local --config app.json`

### 6. Sandboxes (Safe Development)
Sandboxes are isolated DBs linked to a parent org. Use them to safely test schema/trigger changes.
- **List**: `uv run --project cli valstorm sandbox list`
- **Create**: `uv run --project cli valstorm sandbox create <name>`
- **Use (Target)**: `uv run --project cli valstorm sandbox use <name>` (updates `valstorm.json`)
- **Reset to Parent**: `uv run --project cli valstorm sandbox use-parent`
- **Deploy Sandbox to Parent**: `uv run --project cli valstorm deploy app sandbox <sandbox_name> <app_name>`

### 7. Schema & Records (CRUD)
- **List Schemas**: `uv run --project cli valstorm schema list`
- **Get Schema**: `uv run --project cli valstorm schema get <api_name> -o json`
- **Create Record**: `uv run --project cli valstorm record create <schema_name> --data '{"name": "test"}'`

### 8. Authentication & State
Auth is stored in `~/.valstorm/auth_{env}_{profile}.json`. The MCP server and CLI share this token.
- **Check status**: `uv run --project cli valstorm auth whoami`
- **Login via PAT**: `uv run --project cli valstorm auth login pat <YOUR_PAT> --env dev`
- **Check API health**: `uv run --project cli valstorm status`

### 9. Virtual File System (VFS) & Indexing
Agents can interact with the Valstorm file system for RAG, knowledge retrieval, and full CRUD file operations. 
*Note: VFS commands do not currently accept `--profile` or `--env` flags. You must either run them in a directory containing `valstorm.json` OR export `VALSTORM_PROFILE` and `VALSTORM_ENV` before running.*

**Always append `--json` when reading data as an AI.**
- **List Vault/Tree Contents**: `uv run --project cli valstorm vfs list [<vault_id>|/path/to/folder] [--bypass-cache] --json` (omit vault_id to get full vault tree)
- **Path Resolution**: `uv run --project cli valstorm vfs resolve /path/to/folder --json`
- **Full Tree Snapshot**: `uv run --project cli valstorm vfs snapshot [--bypass-cache] --json`
- **Batch Vault Hydration**: `uv run --project cli valstorm vfs batch-vaults <vault_id_1> <vault_id_2> [--bypass-cache] --json`
- **Query VFS Metadata**: `uv run --project cli valstorm vfs query --query "SELECT * FROM file" --json`
- **Single / Recursive Upload**: `uv run --project cli valstorm vfs upload <local_path> --to <vault_id> [-r/--recursive] --json`
- **Single / Recursive Download**: `uv run --project cli valstorm vfs download <item_id> [--dest <dir>] [-r/--recursive] --json`
- **Single Move**: `uv run --project cli valstorm vfs move <item_id> --to <dest_id> [--from <source_id>] --json`
- **Batch Move**: `uv run --project cli valstorm vfs batch-move <item_id_1> <item_id_2> --to <dest_id> [--from <source_id>] --json`
- **Item Metadata Info**: `uv run --project cli valstorm vfs info <item_id> --json`
- **List Version History**: `uv run --project cli valstorm vfs versions <file_id> --json`
- **Set Active Canon Version**: `uv run --project cli valstorm vfs set-active-version <file_id> <version_id_or_number> --json`
- **On-Demand Vector Indexing**: `uv run --project cli valstorm vfs index <file_id|/path/to/file> [--force] --json`
- **Batch Re-indexing**: `uv run --project cli valstorm vfs reindex [--vault <vault_id> | --all] [--limit 100] --json`
- **Delete Items**: `uv run --project cli valstorm vfs delete <item_id_1> [<item_id_2>...] [-f/--force] --json`
- **Rebuild Cache**: `uv run --project cli valstorm vfs rebuild-cache --json`

## Pitfalls & Best Practices
- **JSON Output:** Always append `-o json` (or `--json` for VFS/search/ask) when you need to parse the output programmatically. Terminal tables are hard for LLMs to read reliably.
- **Do NOT guess schema definitions:** Always run `schema get <name>` before attempting to `record create` or `record update` to ensure you are passing the correct field types.
- **Pushing code:** `valstorm push metadata` compares local code against remote and will prompt for confirmation. As an AI, pass specific targets (`valstorm push metadata function my_func.py`) to bypass interactive prompts, or be prepared to handle terminal stdin if prompting occurs.
- **Manifest Diffing:** `valstorm manifest diff` is an incredible tool for AI. Run it after making local file edits, and it will automatically figure out exactly what changed and bundle it into a deployment manifest.

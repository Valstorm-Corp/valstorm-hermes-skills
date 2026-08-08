---
name: file-operations-safety
description: "Use when deleting scratch files or a user file path 404s."
---

# File Operations Safety

Two recurring failure classes in agentic sessions: (1) a cleanup command for one thing accidentally destroys an unrelated deliverable sitting in the same directory, and (2) a user-supplied file path "doesn't exist" even though the file is clearly there, because the filename contains characters that look like plain ASCII but aren't.

## 1. Scope destructive cleanup commands narrowly

**Trigger:** You created a scratch/temp file (a copy for vision analysis, an intermediate script, a throwaway artifact) and now want to remove it once you're done with it.

**Rule:** Never combine the cleanup of a new scratch file with anything else in the same `rm`/delete command unless you have just re-verified every path in that command individually. A single `rm -f fileA fileB` line silently deletes both, even when only `fileA` was ever meant to go — and a prior deliverable (e.g. a compiled context markdown file, a report, a generated asset) sitting in the same directory as today's scratch file is an easy accidental casualty.

**Pitfall observed:** During a session, a `filetree_context.md` deliverable was produced by an earlier task. Later, while cleaning up an unrelated temp screenshot copy made for `vision_analyze`, the cleanup command bundled both paths together (`rm -f temp_copy.png deliverable.md`) and destroyed the deliverable. It had to be regenerated from scratch.

**Concrete practice:**
- Before writing a cleanup command, list out loud (in your own reasoning) exactly which paths you intend to remove and why each one is scratch, not output.
- Prefer one `rm` per distinct piece of cleanup over a single combined command, especially when the files were created in different tasks/turns.
- If you do delete something you shouldn't have, regenerate it immediately (same script/inputs) before proceeding to anything else, and tell the user what happened.
- Treat any file that was explicitly requested by the user, or that you told the user "here is your deliverable at `<path>`", as permanently off-limits to casual cleanup for the rest of the session.

## 2. Unicode lookalike characters in user-supplied filenames (macOS)

**Trigger:** A user references a file by path (e.g. a screenshot) and a direct read/copy/vision call returns "file not found," even though `ls`-ing the parent directory clearly shows a file with that name.

**Root cause:** macOS screenshot filenames (`Screenshot YYYY-MM-DD at H.MM.SS AM/PM.png`) use **U+202F (NARROW NO-BREAK SPACE)** before "AM"/"PM", not a regular space (U+0020). Visually and when the user pastes/types it, it looks identical to a normal space, but exact-string path lookups fail silently.

**Fix:**
- If a plausible-looking path 404s, don't assume the file doesn't exist — list the parent directory programmatically and inspect the raw filename:
  ```python
  import os
  for f in os.listdir(parent_dir):
      if 'Screenshot' in f:
          print(repr(f))  # repr() reveals the \u202f
  ```
- Copy using the exact string returned by the directory listing (or the file object itself), not a manually retyped path.
- This is a stable, durable macOS behavior (not a transient/environment bug) — worth checking for whenever a screenshot- or Finder-exported filename path fails to resolve.

## Related protected skills

- `compile-context` (user-owned) governs compiling multiple files into one context markdown doc — the deliverable-protection lesson above applies directly to that workflow. It's user-owned so this skill can't patch it directly; if compile-context is adopted via `hermes curator adopt compile-context`, fold section 1 above into its Pitfalls list.
- `sketch` (bundled) governs throwaway HTML mockup generation and hit a related but distinct issue this session: Tailwind CDN's default *media-query* dark mode disagreeing with a manual `.dark`-class toggle button, causing broken text contrast on translucent/glass-style variants. That fix (`tailwind.config = { darkMode: 'class' }` right after the CDN script tag, plus verifying contrast in both themes via `browser_vision`) belongs in `sketch`'s pitfalls but the skill is bundled and can't be autonomously patched — flag it to the user if they hit it again.

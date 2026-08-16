---
name: desktop-tree-navigation-patterns
description: Use for desktop tree views, multi-select, and rename inputs.
version: 1.0.0
author: Hermes Agent
---

# Desktop Tree Navigation & Interaction Patterns

Use this skill when developing or debugging tree views, file explorers, Virtual File System (VFS) navigators, and multi-selection interfaces in React and Electron desktop applications.

## Core Interaction Guidelines

### 1. Multi-Selection & Marquee Drag Isolation
When combining click-to-open, folder accordion expand/collapse, native drag-and-drop (DND) reordering, and marquee (rubber-band) multi-selection:
- **Strict Modifier Gating:** Only initialize pointer/mouse drag tracking for marquee selection when a modifier key (`Shift`, `Cmd` / `Ctrl`, or `Option` / `Alt`) is actively held.
- **Immediate Yield on Plain Clicks:** If no modifier key is active on `pointerdown` / `mousedown`, yield immediately. Do not attach global `mousemove` / `mouseup` listeners or clear `selectedPaths` on `mouseup`.
- **DND Conflict Prevention:** Dragging an already-selected row initiates native item moving; modifier dragging across rows initiates the marquee rectangle.

### 2. Controlled Input Focus & Local State Isolation (Zero Re-render Lag)
When implementing inline creation (`New File`, `New Folder`) or rename forms with controlled React inputs:
- **The Pitfall 1 (Ref Callback Selection Trap):** Never use an inline `ref` callback that calls `input.select()` or `input.setSelectionRange()` (e.g. `<input ref={(el) => el?.select()} />`). Because React re-evaluates ref callbacks on every render, each keystroke triggers a state update -> re-render -> ref callback -> `input.select()`. The entire string is re-selected on every keypress, causing the next typed character to overwrite previous characters, continually resetting the field to 1 character.
- **The Pitfall 2 (Root Tree Re-render Lag):** Lifting transient typing state (`value`, `setValue`) to the root tree component causes the entire tree (dozens of folders, files, guide lines, SVG icons) to re-render on every keystroke, causing typing latency.
- **The Solution:** Extract the inline input into an isolated component (`InlineCreationForm`) that manages its own local `useState` for typing. Execute auto-focus and initial text range selection **strictly once on mount** inside `useEffect(() => { ... }, [])`. Only pass the committed string to `onSubmit(value.trim())` when the user submits or presses Enter.

```typescript
interface InlineCreationFormProps {
  depth: number;
  isFile: boolean;
  onSubmit: (name: string) => Promise<void> | void;
  onCancel: () => void;
  initialValue?: string;
}

function InlineCreationForm({ depth, isFile, onSubmit, onCancel, initialValue = "" }: InlineCreationFormProps) {
  const [value, setValue] = useState(initialValue);
  const inputRef = useRef<HTMLInputElement>(null);
  const placeholder = isFile ? "note.md" : "folder-name";

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
      const dotIdx = inputRef.current.value.lastIndexOf(".");
      if (isFile && dotIdx > 0) {
        inputRef.current.setSelectionRange(0, dotIdx);
      } else {
        inputRef.current.select();
      }
    }
  }, [isFile]); // Strictly once on mount

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onSubmit(value.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ paddingLeft: `${depth * 12 + 18}px` }}>
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        onKeyDown={(e) => e.key === "Escape" && onCancel()}
      />
      <button type="submit">Save</button>
      <button type="button" onClick={onCancel}>Cancel</button>
    </form>
  );
}
```

### 3. Cycle-Protected Recursive Tree Traversals
When implementing bulk operations (like `expandAll`, `collapseAll`, or recursive directory caching):
- **The Pitfall:** Traversing cached child arrays (`directoryCache.get(id)`) without cycle detection triggers `RangeError: Maximum call stack size exceeded` if items cross-reference parent nodes or if re-entrant loops iterate over cache entries.
- **The Solution:** Always pass a `visited: Set<string>` into recursive collectors to short-circuit previously evaluated paths, and iterate directly over `directoryCache.keys()` for bulk state updates.

```typescript
const visited = new Set<string>();
const collectKnownFolders = (nodes: any[]) => {
  if (!Array.isArray(nodes)) return;
  for (const n of nodes) {
    const rawId = n.id || n.path || n.name;
    if (!rawId) continue;
    const cleanId = String(rawId).replace("cloud://", "");
    if (visited.has(cleanId)) continue;
    visited.add(cleanId);

    const isFolder = n.isDirectory || n.type === "directory" || cleanId.startsWith("vaul_");
    if (isFolder) {
      expandedSet.add(cleanId);
      expandedSet.add(`cloud://${cleanId}`);
      const cached = directoryCache.get(cleanId);
      if (Array.isArray(cached)) collectKnownFolders(cached);
    }
  }
};
```

### 4. In-Memory Hierarchy Linking (Zero Network Latency)
When fetching tree roots or flat snapshots from database queries (`SELECT * FROM vault`):
- Map all parent-child relationships client-side on mount into a `childrenMap` grouped by `node.parent_vault || "root"`.
- Pre-populate `directoryCache` with normalized keys (`id` and `cloud://id`).
- When the user clicks a folder, its subdirectories are immediately available in memory for instant accordion expansion without waiting for single-folder network requests.

### 5. Multi-Item Clipboard Actions
- When copying multiple selected files/folders (`Cmd+C` or Right-Click Context Menu "Copy Path"), format paths with **newlines (`\n`)** rather than spaces.
- Dynamically update context menu item labels to reflect active multi-selection counts (e.g. `Copy Paths (3)` and `Delete (3)`).

### 6. Section Header & Action Bar Consolidation
- **Flattening Hierarchy:** Avoid stacking redundant vertical toolbar bars (e.g. a global "Workspace" bar above domain-specific "Cloud" and "Local" accordions).
- **Contextual Action Embedding:** Embed quick actions (`Search`, `+ File`, `+ Folder`, `Upload`, `Collapse All`, `+ New Vault`) directly into the section header row with hover reveal (`opacity-0 group-hover:opacity-100 transition-opacity`).
- **Inline Filter Expansion:** When toggling search/filter from the section header, animate an inline filter `<input>` directly underneath the section header bar rather than opening modal dialogs or occupying permanent vertical space.
- **Concise Group Labels:** When grouping under a parent accordion (like "Vaults"), use concise section labels ("Cloud" and "Local") rather than repetitive compound names ("Cloud Vaults" / "Local Vaults").

### 7. Desktop 3-Tier Layering & Column Contrast
- When designing multi-column desktop layouts, use 3-tier layering to prevent flat/washed-out contrast:
  - **Layer 0 (Outer Frame Backdrop):** `bg-[#E5E5EB]` (Light) / `bg-[#070709]` (Dark)
  - **Layer 1 (Sidebar/Utility Islands):** `bg-[#F5F5F7]` (Light) / `bg-[#131316]` (Dark) with `border border-zinc-300/80 dark:border-white/10`
  - **Layer 2 (Hero Main Canvas Island):** Pure `bg-white` (Light) / Pure `bg-[#000000]` (Dark) with `border border-zinc-300/90 dark:border-white/15 shadow-md`
- See `references/desktop-column-layering-and-shell-contrast.md` for full implementation guide.

### 8. Inline Spotlight Search & Autocomplete (Modal Elimination & 60fps Hover)
- Replace blocking full-screen modal search palettes with an interactive navbar spotlight input and a floating glassmorphic autocomplete dropdown (`backdrop-blur-xl bg-white/95 dark:bg-[#18181C]/95 border border-zinc-300/80 dark:border-white/10 shadow-2xl rounded-xl z-50 mt-1.5 max-h-80 overflow-y-auto`).
- Supports `⌘K` focus, real-time VFS file/vault filtering, `ArrowDown`/`ArrowUp` keyboard traversal, `Enter` to open, and `Escape` to close.
- **The Hover Performance Trap (Laggy Mouse Moves):** Never attach `onMouseEnter={() => setSelectedIndex(idx)}` to list items in autocomplete search dropdowns. Firing state setters on every pixel/item the cursor crosses triggers continuous re-renders of the entire search component on every mouse movement, causing severe hover lag and frame drops.
- **The Solution:**
  1. Let native GPU-accelerated CSS (`hover:bg-[#5100FF]/8 hover:text-[#5100FF] dark:hover:bg-[#00C200]/10 dark:hover:text-[#00C200]`) handle mouse hover with **0 JavaScript re-renders**.
  2. Use `selectedIndex` strictly for keyboard navigation (`ArrowDown` / `ArrowUp`).
  3. Wrap result items in `React.memo(SearchItemRow)`.
- See `references/desktop-spotlight-search-and-viewport-locking.md` for complete reference.

### 9. Viewport Height Contract & Dead Space Prevention
- To prevent outer window scrolling and bottom dead space:
  - Outer frame: `h-screen w-screen overflow-hidden flex flex-col`
  - Top navbar: `h-11 shrink-0`
  - Body container: `flex flex-col flex-1 w-full min-h-0 overflow-hidden` (avoid `min-h-full` directly under fixed navbars which overflows `100vh + navbarHeight`)
  - Content viewport: `<main className="flex-1 min-h-0 overflow-y-auto">` for independent internal scrolling.



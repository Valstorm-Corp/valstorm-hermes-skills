# Desktop Spotlight Search & Viewport Locking Patterns

## 1. Top Navbar Spotlight Search (Modal Elimination)
To provide a fast, non-intrusive search experience across desktop applications without disruptive full-screen modal popups:
- **Interactive Inline Input:** The search bar in the top navigation bar acts as a live input rather than a fake modal trigger button.
- **Floating Autocomplete Dropdown:** When focused or typing, render an absolute floating glassmorphic results container directly below the search bar:
  `absolute left-0 right-0 top-full mt-1.5 z-50 bg-white/95 dark:bg-[#18181C]/95 backdrop-blur-xl border border-zinc-300/80 dark:border-white/10 shadow-2xl rounded-xl overflow-hidden`
- **Result Grouping & Categorization:**
  - 📁 **Cloud Vaults & Folders** (`#5100FF` icon)
  - 📄 **Cloud Documents & Files** (`#00C200` icon)
  - ⚡ **Navigation Modules & App Views** (`#F97316` icon)
- **Keyboard Navigation Controls:**
  - `⌘K` / `Ctrl+K`: Global shortcut focuses input and opens dropdown.
  - `ArrowDown` / `ArrowUp`: Traverses `selectedIndex` through the results list.
  - `Enter`: Executes the selected action (opens document in editor, navigates to module) and dismisses dropdown.
  - `Escape`: Clears query, dismisses dropdown, and blurs input.
  - `Click Outside`: Listens to `mousedown` on `document` and closes dropdown when clicking outside the search container ref.

### 1.1. GPU-Accelerated CSS Hover vs State-Driven Hover Jank
- **The Pitfall:** Adding `onMouseEnter={() => setSelectedIndex(idx)}` to list items in an autocomplete search dropdown causes severe hover lag. Every pixel/row the mouse crosses triggers a full component re-render, recalculating `useMemo` dependencies and re-diffing all items on every frame.
- **The Solution:**
  1. Rely exclusively on native GPU-accelerated CSS for mouse hover:
     `className="... hover:bg-[#5100FF]/8 hover:text-[#5100FF] dark:hover:bg-[#00C200]/10 dark:hover:text-[#00C200]"`
  2. Use `selectedIndex` purely for `ArrowDown` / `ArrowUp` keyboard traversal.
  3. Wrap result items in a memoized subcomponent (`React.memo(SearchItemRow)`).

---

## 2. Desktop Viewport Height & Outer Scroll Locking (Dead Space Prevention)

### The Problem:
When an application container has `h-screen flex flex-col` and contains a fixed-height navbar (e.g. `h-11`, 44px), using `min-h-full` on the subsequent flex body child forces that child to be 100% of the viewport (`100vh`). The total layout height becomes `100vh + 44px`, creating window-level outer page scrolling and dead space at the bottom of the screen.

### The Solution:
1. **Outer Window Frame:**
   `<div className="h-screen w-screen overflow-hidden flex flex-col select-none ...">`
2. **Top Navigation Bar:**
   `<header className="h-11 shrink-0 ...">`
3. **Body Multi-Column Container:**
   `<div className="flex flex-col flex-1 w-full min-h-0 overflow-hidden ...">`
   *(Uses `flex-1 min-h-0` to strictly fill the remaining `100vh - 44px` without outer overflow).*
4. **Main Hero Canvas:**
   `<main className="flex flex-col flex-1 h-full min-w-0 overflow-y-auto ...">`
   *(Handles internal content scrolling independently).*

# Desktop 3-Tier Visual Layering & Column Contrast Patterns

## The Problem
When backgrounds across sidebars (`#f4f4f5`), outer frames (`#f4f4f5`), and center working canvases (`#ffffff`) are all within 2-3% of each other, the UI looks flat and washed out in light mode and lacks depth in dark mode.

## The 3-Tier Layering Solution (macOS / Linear / Raycast Style)

### Layer 0: Window Frame / Outer Backdrop
- **Light Mode:** `bg-[#E5E5EB]` (macOS system gray)
- **Dark Mode:** `bg-[#070709]` (deep void backdrop)
- Provides a solid grounding boundary with `p-1.5 lg:p-2` gap spacing.

### Layer 1: Recessed Sidebar & Utility Islands
- **Light Mode:** `bg-[#F5F5F7]` with `border border-zinc-300/80 shadow-sm rounded-xl`
- **Dark Mode:** `bg-[#131316]` with `border border-white/10 shadow-sm rounded-xl`
- Gives navigation sidebars and utility drawers distinct floating toolbar surfaces.

### Layer 2: Hero Main Canvas Island (Pops Forward)
- **Light Mode:** Pure `bg-white` with `border border-zinc-300/90 shadow-md rounded-xl`
- **Dark Mode:** Pure deep canvas `bg-[#000000]` with `border border-white/15 shadow-md rounded-xl`
- The center workspace immediately jumps into the foreground as the primary working area.

### Top Navigation Bar
- `bg-white/95 dark:bg-[#0E0E12]/95 backdrop-blur-md border-b border-zinc-300/80 dark:border-white/10 shadow-xs`

## Decoupling Desktop Shell Layouts from Shared Web Packages
- Do not force the desktop Electron app to consume shared web layout packages that contain web marketing banners or responsive browser workarounds.
- Decouple the desktop shell into dedicated desktop components (`DesktopThreeColumnLayout.tsx`, `DesktopTopNavbar.tsx`, `DesktopMobileSidebar.tsx`).
- Wire desktop-native features directly into the local shell: macOS Spotlight-style `⌘K` command triggers, direct column toggle icon buttons (`PanelLeft`, `PanelRight`), live pulsing status pills (`#00C200` glowing indicator), and local persistent state while maintaining strict compliance with the monorepo height propagation contract (`min-h-full flex flex-col flex-1`).

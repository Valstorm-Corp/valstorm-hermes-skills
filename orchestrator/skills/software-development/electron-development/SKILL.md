---
name: electron-development
description: "Use for Electron desktop apps: external links and IPC."
---

# Electron Development

Use this skill when developing or debugging Electron desktop applications. It captures non-obvious default behaviors and known patterns for overriding them.

## Trigger
- Working within an Electron codebase (e.g., `main.ts`, `preload.js`).
- Dealing with window management, external links, IPC, or native OS integrations.

## Pitfalls and Patterns

### Opening Links in the Default OS Browser
By default, standard HTML links (even with `target="_blank"`) will open a new Electron application window rather than opening the user's default web browser (like Chrome, Safari, or Edge).

**The Fix:**
You must intercept window creation in the main process (usually `main.ts` or `index.ts`) using `setWindowOpenHandler` on the `webContents` of your `BrowserWindow`. 

```typescript
import { shell } from 'electron';

// Inside your createWindow function:
const mainWindow = new BrowserWindow({ /* ... */ });

// Intercept window.open and target="_blank" to open in default OS browser
mainWindow.webContents.setWindowOpenHandler(({ url }) => {
  shell.openExternal(url);
  return { action: 'deny' };
});
```

*Note: Always return `{ action: 'deny' }` to prevent Electron from still spawning a new application window after launching the OS browser.*

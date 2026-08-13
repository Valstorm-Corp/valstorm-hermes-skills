---
name: react-performance-patterns
description: Use for React performance and bypassing state on streams.
tags: [react, frontend, performance, state, ui]
---

# React Performance Patterns

Use these patterns when optimizing React component performance for the Valstorm frontend or extension, particularly when dealing with real-time streams or hardware inputs.

## 1. High-Frequency Text Updates (Bypassing State)
When a component receives extremely high-frequency events—like partial Speech-to-Text transcripts from a WebSocket arriving dozens of times a second—**do not use `setValue()` (React state) to store the intermediate partial string.**

Using React state causes the entire component to re-render (and invokes expensive `useEffect` hooks like auto-resize) on every syllable, leading to severe input choppiness and dropped frames.

### Solution: Direct DOM Mutation
1. Use `useRef` to target the underlying `<textarea>` or `<input>` element.
2. For intermediate/partial updates, manually mutate the DOM `textareaRef.current.value = partialText`.
3. Only call React's `setValue()` when the stream/phrase is complete (`isFinal === true`) to re-sync the final text back into the framework's reactive tree.

```typescript
const snapshotRef = useRef('');
const handleTranscript = useCallback((text, isFinal) => {
  if (isFinal) {
    snapshotRef.current = snapshotRef.current + (snapshotRef.current ? ' ' : '') + text;
    // Final sync
    setValue(snapshotRef.current);
    onChangeRef.current?.(snapshotRef.current);
  } else {
    const partialText = snapshotRef.current + (snapshotRef.current ? ' ' : '') + text;
    // DO NOT call setValue(partialText) to avoid full component re-renders and choppiness!
    // Bypass React state entirely and update the DOM directly:
    if (textareaRef.current) {
      textareaRef.current.value = partialText;
    }
  }
}, []);
```
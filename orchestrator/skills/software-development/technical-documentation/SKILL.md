---
name: technical-documentation
description: Use when authoring Markdown and Mermaid diagrams.
version: 1.0.0
---

# Technical Documentation Standards

Use this skill when authoring or refactoring Markdown documentation, READMEs, or architectural guides.

## Mermaid Diagrams & Visualizations

**Pitfall:** Generating a Mermaid diagram that maps a large system or folder structure 1:1. This results in massive, unreadable charts that overwhelm the user and break document flow.
**Solution:** Abstract the complexity. Map the top-level structure, but only expand a *single representative branch* to serve as a visual template (e.g., showing the full structure of the 'Sales' department, while leaving the other departments as collapsed single nodes).

## Naming Conventions (Canon vs. WIP)

When structuring documentation repositories that serve as AI context or living knowledge bases:

*   **Point-in-Time Docs (Snapshots):** Use date prefixes (e.g., `2024-10-24-Sales-Sync.md`). These are historical records that should sort chronologically. Even with system versioning, the document identity is tied to the date.
*   **Living Documents (Canon):** Use semantic Kebab-case (e.g., `api-authentication.md`). The filename acts as a permanent URL slug. Do not include version numbers or dates in the filename; rely on system metadata/versioning to track state (Draft, In Review, Published).

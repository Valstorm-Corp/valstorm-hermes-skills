---
name: compile-context
description: Compiles a list of file paths into a single Markdown file to build a context document without blowing up the context window.
---

# Context Compiler

When the user provides a list of file paths and asks you to compile them into a context file (e.g., `context.md`), do **NOT** use the `read_file` tool to read their contents into your context window. This will cause massive token truncation and background delegation failures.

Instead, use a Python script executed via the `write_file` + `terminal` combination to read the files and write them directly to disk into a single Markdown file.

## Trigger
- The user provides multiple file paths.
- The user asks to "compile context", "create a markdown file with these files", or "aggregate these files".

## Steps
1. Identify the target output file path (e.g., `vfs_context.md` in the current directory or a specified path).
2. Identify the list of input file paths.
3. Write a Python script (e.g., `generate_context.py`) using `write_file` that reads each file and writes its content to the output Markdown file in a structured format.
4. Execute the Python script using the `terminal` tool: `python3 generate_context.py`.
5. Verify the file was created and inform the user.

## Example Python Script Pattern
```python
import sys

output_path = "/Users/jared/Documents/Code/monorepo/compiled_context.md"
files = [
    "/path/to/file1.py",
    "/path/to/file2.tsx"
]

with open(output_path, "w") as out:
    out.write("# Compiled Context\n\n")
    for f in files:
        try:
            with open(f, "r") as infile:
                content = infile.read()
            out.write(f"## {f}\n\n```\n{content}\n```\n\n")
        except Exception as e:
            out.write(f"## {f}\n\n```text\nError reading file: {e}\n```\n\n")

print(f"Context successfully aggregated into {output_path}")
```

## Pitfalls
- **NEVER** use `read_file` for this task. It will flood the agent's context window.
- Ensure the python script handles file reading errors gracefully (e.g., file not found).
- Use absolute paths in the Python script to avoid working directory confusion.
---
name: bash-scripting
description: Best practices and pitfalls when modifying Bash scripts.
category: software-development
---

# Bash Scripting

When writing, modifying, or debugging Bash shell scripts (e.g., build scripts, sync scripts, automation), follow these safety practices:

## Sourcing vs Execution Safety (The `set -e` Trap)

If a script uses `set -e`, `exit`, or `return` and a user mistakenly runs it via `source script.sh` (or `. script.sh`) instead of executing it directly (`./script.sh`), it will instantly terminate their entire terminal session (because `exit` inside a sourced script exits the parent shell).

**Always protect standalone operational scripts with a source-guard at the top:**
```bash
#!/bin/bash

# Prevent the script from closing the user's terminal if they mistakenly source it
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  echo "❌ Error: Do not source this script. Run it directly: ./script.sh or bash script.sh"
  return 1 2>/dev/null || exit 1
fi

# Exit on error
set -e

# ... rest of script
```

## Directory Context
Never assume the script is executed from the directory it resides in. If your script interacts with files relative to itself, resolve its absolute directory first:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
```

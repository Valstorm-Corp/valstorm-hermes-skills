---
name: vite-application-development
description: Use when building or verifying a Vite web application.
version: 1.0.0
---

# Vite Application Development

## Trigger
Use when creating, extending, or verifying a Vite application, especially React interfaces with user-editable calculations or other business logic.

## Workflow

1. Inspect the target directory and package tooling before creating files. Pick a dedicated, descriptive application directory.
2. Scaffold explicitly: `npm create vite@latest <app-directory> -- --template react` (or the requested template).
3. The scaffold command creates the application directory but does not change the shell working directory. Run `npm install` from `<app-directory>`, not the parent directory.
4. Inspect generated `package.json`, source entrypoint, app component, global styles, and Vite config before replacing starter code.
5. For non-trivial business logic, extract a dependency-free module under `src/` and test it with Vitest. Add `vitest` and a `test` package script when missing.
6. Follow RED-GREEN-REFACTOR: add one missing behavior test, run it to observe the expected failure, implement the smallest change, then rerun the suite.
7. Build the UI from the tested module. Keep user input state in the component and treat calculated values as derived state.
8. Provide labels, keyboard-accessible controls, inline validation, reset behavior, responsive layout, and currency/number formatting appropriate to the domain.
9. Verify completion with the full test suite, lint, `npm run build`, and a browser smoke check where available.

## Calculator and estimator rules

- Keep math, input normalization, and validation out of JSX.
- Do not silently present a valid-looking estimate for invalid inputs. Return validation errors with the calculation result and surface them in the UI.
- For percentage-to-headcount allocation, independent `Math.round` calls can over- or under-allocate. Use largest-remainder allocation: floor every raw amount, then distribute the remaining people to the largest fractional remainders. Break ties using the original tier order.
- Test default/example figures, annualization, configurable fees, invalid distributions, and the invariant that allocated headcount equals requested headcount.
- Use `Intl.NumberFormat` for displayed currencies; do not hard-code locale-specific number formatting.

## Verification checklist

- [ ] Dependencies installed in the generated application directory.
- [ ] Package scripts include test, lint, dev, and build as appropriate.
- [ ] New business-logic tests were observed failing before the implementation change.
- [ ] `npm test` passes.
- [ ] `npm run lint` passes.
- [ ] `npm run build` passes.
- [ ] The browser shows the intended default state and no console errors.
- [ ] Key edited values update the calculated result.

## Pitfalls

- Do not chain `npm install` after a scaffold command without changing directories; it will search for a parent `package.json` and fail.
- Do not use rounded per-tier values when the sum must exactly equal a total.
- Do not add a production dependency merely for testable pure calculations.
- Do not stop after a successful dev server start: unit tests and a production build catch different failures.

## References

- `references/pricing-calculation-patterns.md` — reusable allocation, validation, and test cases for usage-based pricing calculators.

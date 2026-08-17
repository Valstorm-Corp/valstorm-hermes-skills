# Pricing Calculator Patterns

## Largest-remainder allocation

Use when whole people must be distributed from percentage shares without changing the requested headcount.

1. Calculate `raw = employeeCount * share / 100` for every tier.
2. Assign `floor(raw)` to every tier.
3. Calculate `remaining = employeeCount - sum(floor(raw))`.
4. Sort tiers by descending `raw - floor(raw)`; break ties by original tier order.
5. Give one additional person to each of the first `remaining` tiers.

This is deterministic and guarantees the sum of allocations equals the team size when the shares total 100%.

## Recommended result contract

Return rows with normalized tier values, allocated people, and per-tier monthly cost. Also return:

- monthly usage cost
- platform fee
- all-in monthly total
- annual total
- per-employee usage and all-in rates (or `null` for zero employees)
- total share
- `isValid`
- readable validation errors

## Minimum tests

- Given model figures calculate the expected tier allocations and usage total.
- Configurable platform fee changes the monthly and annual total.
- A fractional distribution still allocates exactly the requested number of employees.
- Shares other than 100% are invalid.
- Negative or non-numeric currency/percentage values are invalid.

# Valstorm OS Brand Palette Styling Guidelines

When implementing or modernizing UI components, sidebars, navigation panels, and active indicators in Valstorm:

## Core Color Tokens
- **Valstorm Green (`#00C200`):** Primary action color, active status badges (`● System Operational`), and energetic interactive highlights.
- **Electric Purple (`#5100FF`):** Secondary interactive washes, navigation active pills (`bg-[#5100FF]/10 text-[#5100FF] dark:bg-[#00C200]/15 dark:text-[#00C200]`), and primary icons.
- **Impact Orange (`#F97316`):** High-impact callouts, alerts, and warning badges.
- **Power Yellow (`#FFB400`):** Secondary accents, pending states, and tags.

## Signature Tri-Color Gradient
- `linear-gradient(to right, #F97316, #00C200, #5100FF)` (Orange -> Green -> Purple)
- Used on workspace avatars, Task Workflow action button borders, and primary CTA cards.

## Surface & Canvas Theme Standards
- **Light Theme:** `#ffffff` canvas surfaces + `#f4f4f5` sidebars + `rgba(0,0,0,0.08)` borders.
- **Dark Theme:** `#09090b` canvas surfaces + `#18181b` sidebars + `rgba(255,255,255,0.08)` borders.
- **Avoid:** Bland monochromatic gray washes without brand accents.

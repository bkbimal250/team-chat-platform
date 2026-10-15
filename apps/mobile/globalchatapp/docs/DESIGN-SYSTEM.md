# Design system

Tokens live under `lib/theme/tokens/`:

- **Colors** — primary `#635BFF`, light/dark surfaces, semantic success/error
- **Spacing** — 4pt scale, minimum touch target 48dp
- **Radii** — cards, bubbles, pills
- **Typography** — `GcTypography.textTheme`
- **Shadows** — `GcShadows.card`

Use `GcTheme.light()` / `GcTheme.dark()` via `MaterialApp`. Appearance override: Settings → Appearance (`themeModeProvider`).

Reusable widgets: `lib/components/ui/` (`GcAvatar`, `GcEmptyState`, `GcBadge`, `GcScopeChip`, …).

Interaction patterns follow familiar messaging apps; visuals are **GlobalChat-original** (not a WhatsApp clone).

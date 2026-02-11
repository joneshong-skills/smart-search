# Observations — smart-search

## Pending

## Resolved

### 2026-02-11 — Perplexity UI redesign verified (dismissed)
- **Resolution**: Live test confirmed Perplexity automation via Playwright still works correctly. The Feb 2026 UI redesign (chat bubbles, sidebar) is purely visual — Playwright's browser_snapshot uses accessibility tree which is unaffected. Navigate → snapshot → type → submit → wait → snapshot flow works as documented. No action needed.

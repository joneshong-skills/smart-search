# Observations — smart-search

## Pending

## Resolved

### 2026-02-11 — v0.3.0 Step 0 GitHub Detection + consistency fixes
- **Resolution**: Added Step 0 (WebSearch auto-detect for ambiguous queries). During optimizer review, found and fixed: (1) duplicate "Type C" labels in search-strategy.md — removed "Repo Architecture Questions" as standalone type, folded into Type A; (2) version bumped 0.2.0 → 0.3.0; (3) added Route vs Type clarification note. Agent consensus: 3/3 Advocate/Skeptic/Pragmatist agreed on fixes 1, 2, 4; majority (2/3) on fix 3.

### 2026-02-11 — Perplexity UI redesign verified (dismissed)
- **Resolution**: Live test confirmed Perplexity automation via Playwright still works correctly. The Feb 2026 UI redesign (chat bubbles, sidebar) is purely visual — Playwright's browser_snapshot uses accessibility tree which is unaffected. Navigate → snapshot → type → submit → wait → snapshot flow works as documented. No action needed.

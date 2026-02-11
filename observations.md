# Observations — smart-search

## Pending

### 2026-02-11 — Perplexity UI redesign (chat bubbles, new sidebar)
- **Category**: tech
- **Evidence**: Feb 2026 Perplexity changelog confirms UI redesign with chat bubble messages, universal tabs, sidebar restructure.
- **Research**: Changes are live on web. Playwright automation uses accessibility tree via browser_snapshot (not CSS selectors), so impact may be minimal. But element refs and DOM structure likely changed.
- **Confidence**: Medium
- **Trigger**: Next Perplexity search via smart-search skill — if automation fails or returns unexpected results, update the Perplexity workflow steps.

## Resolved

### 2026-02-15 — Async deck generation by default
- **Friction**: Slide/deck generation blocked the main response flow and increased user wait time.
- **Fix**: Added background-mode (`nohup ... &`) rule with PID/log/output-path reporting.
- **Rule**: For presentation requests, finish research synchronously, then run deck generation asynchronously unless user asks to wait.

### 2026-02-22 — browser agent cannot access Playwright MCP tools
- **Friction**: Perplexity searches silently fell back to WebSearch since ~2/11. `browser` agent has `Tools: Bash, Read, Write` only — no ToolSearch, so it cannot load deferred Playwright MCP tools. The SKILL.md fallback "if Playwright is unavailable" triggered every time.
- **Fix**: Changed Perplexity delegation from `browser` to `general-purpose` agent (has `Tools: *` including ToolSearch). Added explicit ToolSearch step in Route A/D instructions.
- **Rule**: Any sub-agent needing MCP tools must have `ToolSearch` access. Only `general-purpose` (`Tools: *`) has this. Never delegate MCP-dependent work to specialized agents (`browser`, `researcher`, etc.). This includes ALL MCP tools: Playwright, DeepWiki, Context7, etc.

### 2026-02-25 — GitNexus Next-Step Hints pattern adopted
- **Friction**: After MCP tool calls, AI agents sometimes lost track of optimal next actions, leading to unnecessary queries or hallucinated steps.
- **Fix**: Implemented `hints.ts` module in both `sandbox-executor` (2 tools) and `kas-memory` (9 tools) MCP servers. Each tool response now appends a contextual `💡 Next:` hint based on tool name + result state (success/failure/empty).
- **Rule**: When building MCP tools, always include a next-step hint in tool responses. This is a low-cost, high-impact pattern that replaces complex coordinator agents with simple self-guiding workflows.

### 2026-03-01 — MCP audit: Playwright MCP removed, WebSearch+WebFetch as primary
- **Friction**: Playwright MCP × 2 cost ~7,200 tokens schema per session. Perplexity-via-Playwright was fragile (browser agent ToolSearch issue from 2/22, page load failures). The entire Perplexity route was a complex 6-step MCP chain for what WebSearch does natively.
- **Fix**: Removed both Playwright MCP servers. All search routes (A/D/E) now use WebSearch+WebFetch inline. Playwright CLI (`@playwright/mcp`) preserved for rare browser automation needs via Bash, with dynamic session profiles synced from master.
- **Rule**: For search skills, prefer built-in tools (WebSearch+WebFetch) over MCP-dependent browser automation chains. MCP servers are justified only when they provide capabilities not available through simpler tools. The 68 vs 3,600 token difference per task is decisive.

### 2026-03-04 — FSM refactor: SKILL.md 555→247 lines
- **Friction**: Deep Research Pipeline (Route F) 新增後 SKILL.md 膨脹至 555 行，超過 500 行上限。線性流程敘述難以一眼看清控制流。
- **Fix**: 用 FSM 狀態圖（PRE_CHECK → CLASSIFY → DEPTH_CHECK → EXECUTE → SYNTHESIZE → REPORT_SAVE）取代線性敘述。253 行執行細節抽至 3 個 `references/` 檔案（community-search, deep-research-pipeline, report-io）。SKILL.md 只保留狀態轉移 + 每個 Route 一句話摘要。
- **Rule**: 當 Skill 流程有 3+ 分支（條件判斷）時，用 FSM 狀態圖取代線性敘述，詳細執行步驟抽至 `references/`。SKILL.md = 決策樹 + 指針，references = 執行手冊。

### 2026-02-27 — last30days-skill analysis: 3 patterns adopted
- **Friction**: Community Search returned flat WebSearch results with no engagement weighting, no entity drill-down, and synthesis was basic concatenation.
- **Fix**: Added 3 patterns to SKILL.md v0.4.0:
  1. **Phase 2 Entity Drill-Down** — extract @handles/r/subreddits from Phase 1, run targeted follow-up searches
  2. **Judge Agent Synthesis** — cross-source verification with engagement weighting and contradiction flagging
  3. **feedscan integration note** — future Core Module will replace raw WebSearch with normalized, scored results
- **Rule**: For community/trend queries, always do two-phase search (broad → entity → targeted) and synthesize with cross-validation, not concatenation. Engagement signals (upvotes, likes) should weight result priority.

### 2026-03-30 — Report API endpoint drift: 8830 → 10000/intelflow, raw curl → SDK
- **Friction**: SKILL.md still referenced old `localhost:8830/api/research/*` endpoints. The intelflow module lives on Core API (port 10000) at `/api/intelflow/*`. Raw curl also lacked `X-Internal-Key` auth header, causing 401 "Not authenticated". Report silently fell back to local file write, never reaching the DB.
- **Fix**: Replaced all curl commands with `sdk_client.intelflow.IntelflowClient` calls. SDK handles auth (`X-Internal-Key` via `CORE_INTERNAL_API_KEY` env), `space_id`, and error handling automatically. Also fixed `sources` field from `list[str]` to `list[dict]`.
- **Rule**: Never use raw curl for Core API calls in skills — always use `sdk_client.*Client`. The SDK handles auth, space_id, and error wrapping. When an API "works in browser but fails in skill", check auth first.

### 2026-04-01 — SKILL.md 從未套用 2026-03-30 修正：lesson 寫了但 SKILL.md 沒改
- **Friction**: 2026-03-30 已記錄修正方案（raw curl → SDK/CLI），但 SKILL.md 仍保留 `localhost:8830` 的 raw curl 指令。每次搜尋都靜默 fallback 到本地檔案。
- **Fix**: SKILL.md Pre-Search + Report Output 兩節全面改寫為 `core/cli/intelflow.py` CLI 調用。移除 file fallback，改為失敗時明確警告使用者。
- **Rule**: Lesson 記錄修正方案後，必須同步修改 SKILL.md。Lesson 是診斷紀錄，不是修正本身——「知道問題」≠「修好問題」。

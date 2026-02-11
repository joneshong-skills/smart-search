---
name: smart-search
description: >-
  This skill should be used when the user asks to "search for information",
  "look up documentation", "find the latest news", "research a topic",
  "query library docs", "搜尋", "查一下", "幫我找",
  or discusses searching, researching, looking up documentation,
  finding current information, or querying technical references.
version: 0.3.0
---

# Smart Search

Hybrid search tool combining DeepWiki (free, unlimited), Context7 (precise, 1000/month),
and Perplexity Pro via Playwright (current events & broad research).
Auto-selects the best search backend based on query type, complexity, and quota.

## Key Insight: DeepWiki vs Context7

Both can answer library/framework questions. The real differences:

| | DeepWiki | Context7 |
|---|---|---|
| **即時性** | 索引間隔數週（~2-4 weeks） | 索引間隔 1-5 天 |
| **精準度** | 架構級理解，細節可能有缺漏 | 版本精準的 API 用法 + code snippets |
| **額度** | 免費無限 | 1000 次/月 |
| **適合** | 架構問題、一般用法、初步查詢 | 精確 API 參數、最新語法、複雜問題 |

## Search Backend Selection

### Step 0 — GitHub Code Detection (Auto-Detect)

When the query subject is **ambiguous** (could be code or non-code), auto-detect before classifying:

**When to trigger**: The query mentions a name/term that COULD be a GitHub repo/library but the user
did NOT explicitly say it's code-related. Skip this step if:
- Query already contains clear code signals (import, API, hook, config, repo, GitHub, etc.)
- Query is obviously non-code (news, 今天, 新聞, 比較, 推薦, etc.)
- Query includes `owner/repo` format (e.g., `vercel/next.js`)

**How**:
1. Use `WebSearch` with query: `"{subject}" github` (keep it minimal for speed)
2. Check results — if a GitHub repository appears prominently in the top results → treat as **GitHub Code Query**
3. If no GitHub repo found → proceed to normal classification (Step 1)

**Example**:
- User asks "Apollo 怎麼用" → WebSearch `"Apollo" github` → finds `apollographql/apollo-client` → GitHub Code Query
- User asks "Apollo 登月計畫" → WebSearch `"Apollo" github` → top results are NASA/history → NOT code → normal classification
- User asks "React useEffect" → skip Step 0 (clear code signal) → directly classify as Library docs

### Step 1 — Classify the Query

| Type | Keywords / Signals | Backend |
|------|-------------------|---------|
| **GitHub Code Query** (detected by Step 0 or explicit signals) | repo name + GitHub match, import, API, hook, config, props, function, component, repo, architecture, source code | **DeepWiki + Perplexity** (parallel) |
| **Library/Framework docs** (no ambiguity, clearly a known lib) | import, API, hook, config, props, function, component | **DeepWiki first** → Context7 補充 |
| **Current events** | today, latest, news, 今天, 最新, 2026 | **Perplexity** |
| **General research** | best practice, comparison, vs, tutorial, 推薦, 比較 | **Perplexity** |
| **Hybrid** | Multiple types detected | Combine (parallel when possible) |

### Step 2 — Library/Framework Query Escalation Chain

For library documentation queries, follow this priority:

```
1. DeepWiki (免費, 無限) ─── 先用這個
   │
   ├─ 回答完整且精準 → 直接回覆，不消耗 Context7 額度
   │
   └─ 回答不夠精準/有缺漏/需要最新 API 細節
       │
       2. Context7 (精準, 1000次/月) ─── 補充或取代
       │  └─ 先 check 額度，用完則跳到 3
       │
       3. Perplexity (即時, Pro 會員) ─── 最後手段
          └─ 搜尋 "{library} {query} documentation latest"
```

### Step 3 — Check Context7 Quota (Before Every Context7 Call)

```bash
python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py check
```

- `available: true, warning: false` → Use Context7
- `available: true, warning: true` → Use Context7 but mention remaining quota
- `available: false` → **Fall back to DeepWiki**, then Perplexity if needed

After each successful Context7 call:

```bash
python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py increment
```

### Step 4 — Execute Search

#### Route A: DeepWiki + Perplexity (GitHub Code Query — Default for Step 0 matches)

Use when: Step 0 detected a GitHub repo, or user is clearly asking about a GitHub project/library.

Run **both in parallel** using the Task tool (subagent_type: general-purpose):

**DeepWiki leg**:
1. Determine the GitHub `owner/repo` (use the repo found in Step 0, or map library name → repo)
2. Call `mcp__deepwiki__ask_question` with repo name and question

**Perplexity leg**:
1. `mcp__playwright__browser_navigate` → `https://www.perplexity.ai/`
2. `mcp__playwright__browser_snapshot` → locate search input ref
3. `mcp__playwright__browser_type` → ref=search-input, text=query, submit=true
4. `mcp__playwright__browser_wait_for` → time=12
5. `mcp__playwright__browser_snapshot` → extract answer text

Synthesize both results, noting which info came from which source.

#### Route B: DeepWiki First → Context7 Supplement (Known Library, No Ambiguity)

For well-known library queries where there's no name ambiguity:

1. Determine the GitHub `owner/repo` for the library (e.g., React → `facebook/react`, Next.js → `vercel/next.js`)
2. Call `mcp__deepwiki__ask_question` with repo name and question
3. Evaluate answer quality — if sufficient, return directly
4. If answer has gaps or needs precise API details, escalate to Context7

#### Route C: Context7 (Precision Supplement)

Only use when:
- DeepWiki answer is imprecise or incomplete
- Query requires exact API signatures, parameters, or latest syntax
- User explicitly requests most up-to-date documentation

Steps:
1. Run `usage_tracker.py check` to verify quota
2. Call `mcp__context7__resolve-library-id` with library name
3. Call `mcp__context7__query-docs` with resolved library ID and query
4. Run `usage_tracker.py increment` to record the call
5. Return with source attribution and quota info

#### Route D: Perplexity (Current Events, Research & Fallback)

Use for:
- Current events, news, trending topics
- General research, comparisons, best practices
- Fallback when both DeepWiki and Context7 are insufficient or unavailable

Steps:
1. `mcp__playwright__browser_navigate` → `https://www.perplexity.ai/`
2. `mcp__playwright__browser_snapshot` → locate search input ref
3. `mcp__playwright__browser_type` → ref=search-input, text=query, submit=true
4. `mcp__playwright__browser_wait_for` → time=12
5. `mcp__playwright__browser_snapshot` → extract answer text
6. Parse accessibility tree for paragraphs, citations, source links
7. Return synthesized answer with Perplexity source links

#### Route E: Hybrid (Multiple Sources)

Run applicable routes in parallel using the Task tool (subagent_type: general-purpose).
Synthesize results, noting which info came from where.

## Context7 Quota Exhaustion Fallback

When Context7 monthly limit is reached:

```
Library query → DeepWiki (always available)
                 │
                 └─ If still insufficient → Perplexity search
                    "{library} {specific API} documentation site:official-docs-url"
```

Do NOT skip DeepWiki and go straight to Perplexity — DeepWiki is free and often sufficient.

## Response Format

Always include in the final response:

1. **Answer** — The synthesized information
2. **Sources** — Which backend(s) provided the data
3. **Quota** (if Context7 was used) — Current month usage / limit

Example footer:
```
---
Sources: DeepWiki (vercel/next.js) + Context7 (Next.js docs v15)
Context7 quota: 43/1000 (February 2026)
```

## Quota Management Commands

```bash
python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py status
```

## Important Notes

- **DeepWiki first** — free and unlimited, always try it before spending Context7 quota
- Context7 is the **precision tool** — save it for when DeepWiki's answer isn't enough
- Context7 quota exhausted → **DeepWiki fallback** (not Perplexity)
- Perplexity Pro membership valid until **2026/12/28**
- Context7 limit resets on the 1st of each month automatically
- Use `mcp__playwright__browser_console_messages` (level=error) if Perplexity page fails to load

## Additional Resources

### Reference Files
- **`references/search-strategy.md`** — Detailed decision tree, query classification keywords, Perplexity workflow steps, and usage tracking documentation

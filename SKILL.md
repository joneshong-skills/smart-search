---
name: smart-search
description: >-
  This skill should be used when the user asks to "search for information",
  "look up documentation", "find the latest news", "research a topic",
  "query library docs", "搜尋", "查一下", "幫我找",
  or discusses searching, researching, looking up documentation,
  finding current information, or querying technical references.
version: 0.3.3
tools: Task, WebSearch, WebFetch, Bash
argument-hint: <search query in any language>
---

# Smart Search

Hybrid search tool combining DeepWiki (free, unlimited), Context7 (precise, 1000/month),
and Perplexity Pro via Playwright (current events & broad research).
Auto-selects the best search backend based on query type, complexity, and quota.

## Agent Delegation

Delegate individual search legs to the `researcher` agent (one per backend or topic angle). For Perplexity/browser-based searches, use the `browser` agent instead.

```
Main context (query classification + synthesis)
  └─ Task(subagent_type: researcher, prompt: "Search DeepWiki for {repo}: {question}. Return ONLY a concise summary of findings.")
  └─ Task(subagent_type: browser, prompt: "Search Perplexity for: {query}. Return ONLY the answer text and source URLs.")
```

Fallback: if `researcher` is unavailable, run WebSearch + WebFetch inline.

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
~/.local/bin/python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py check
```

- `available: true, warning: false` → Use Context7
- `available: true, warning: true` → Use Context7 but mention remaining quota
- `available: false` → **Fall back to DeepWiki**, then Perplexity if needed

After each successful Context7 call:

```bash
~/.local/bin/python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py increment
```

### Step 4 — Execute Search

#### Route A: DeepWiki + Perplexity (GitHub Code Query — Default for Step 0 matches)

Use when: Step 0 detected a GitHub repo, or user is clearly asking about a GitHub project/library.

Run **both in parallel** using the Task tool (subagent_type: general-purpose):

**DeepWiki leg**:
1. Determine the GitHub `owner/repo` (use the repo found in Step 0, or map library name → repo)
2. Query DeepWiki via mcpproxy: `call_tool_read(server="deepwiki", tool="ask_question", arguments={repoName, question})`

**Perplexity leg** (delegate to `browser` agent):
Prompt the browser agent: "Use camoufox-cli with --session perplexity --headed --persistent ~/.camoufox-profiles/master. Open https://www.perplexity.ai/, wait for page load, use snapshot -i to find the search input, fill it with the query, press Enter, wait 12s, snapshot again to extract answer text and source links. Return ONLY the synthesized answer and source URLs."

Synthesize both results, noting which info came from which source.

#### Route B: DeepWiki First → Context7 Supplement (Known Library, No Ambiguity)

For well-known library queries where there's no name ambiguity:

1. Determine the GitHub `owner/repo` for the library (e.g., React → `facebook/react`, Next.js → `vercel/next.js`)
2. Query DeepWiki via mcpproxy: `call_tool_read(server="deepwiki", tool="ask_question", arguments={repoName, question})`
3. Evaluate answer quality — if sufficient, return directly
4. If answer has gaps or needs precise API details, escalate to Context7

#### Route C: Context7 (Precision Supplement)

Only use when:
- DeepWiki answer is imprecise or incomplete
- Query requires exact API signatures, parameters, or latest syntax
- User explicitly requests most up-to-date documentation

Steps:
1. Run `usage_tracker.py check` to verify quota
2. Resolve library via mcpproxy: `call_tool_read(server="context7", tool="resolve-library-id", arguments={libraryName})`
3. Query docs via mcpproxy: `call_tool_read(server="context7", tool="query-docs", arguments={libraryId, query})`
4. Run `usage_tracker.py increment` to record the call
5. Return with source attribution and quota info

#### Route D: Perplexity (Current Events, Research & Fallback)

Use for:
- Current events, news, trending topics
- General research, comparisons, best practices
- Fallback when both DeepWiki and Context7 are insufficient or unavailable

Steps:
1. Delegate to `browser` agent with prompt: "Use camoufox-cli with --session perplexity --headed --persistent ~/.camoufox-profiles/master. Open https://www.perplexity.ai/, use snapshot -i to find search input, fill with query, press Enter, wait 12s, snapshot to extract answer and source links. Return the synthesized answer with source URLs."
2. Parse the browser agent's response for answer text and source URLs

**Fallback when browser agent is unavailable**: Fall back to `WebSearch` for the query, then use `WebFetch` to retrieve and extract content from the most relevant result URLs. This provides similar coverage to Perplexity without requiring a browser session.

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

## Pre-Search: Check Existing Reports

Before executing any search, check if a similar report already exists via intelflow CLI:

```bash
~/.local/bin/python3 ~/workshop/core/cli/intelflow.py reports check "<user query>" --threshold 0.7
```

- If similar report(s) found:
  - Present title, date, and similarity score
  - Ask: "找到相似的研究報告，要直接查看還是重新搜尋？"
  - If user wants to view: `~/.local/bin/python3 ~/workshop/core/cli/intelflow.py reports get <id>`
  - If user wants fresh search: proceed to normal search flow
- If no similar reports found: proceed to normal search flow
- If the CLI call fails (Core API down), skip this step and proceed normally (graceful degradation)

## Report Output

Every search result MUST be saved to the intelflow DB. **NEVER fall back to local file write.**

**Steps**:
1. After synthesizing the final answer, save via intelflow CLI:
   ```bash
   ~/.local/bin/python3 ~/workshop/core/cli/intelflow.py reports create \
     --title "<Title derived from query>" \
     --query "<original user query>" \
     --content "<Full synthesized report content in Markdown>" \
     --tags "tag1,tag2,tag3" \
     --sources '[{"url":"<url1>","label":"<label1>"},{"url":"<url2>","label":"<label2>"}]' \
     --skill smart-search
   ```
   For content with special characters, use a heredoc or temp file:
   ```bash
   CONTENT=$(cat <<'CONTENT_EOF'
   <Full Markdown report>
   CONTENT_EOF
   )
   ~/.local/bin/python3 ~/workshop/core/cli/intelflow.py reports create \
     --title "..." --query "..." --content "$CONTENT" --tags "..." --sources '...' --skill smart-search
   ```

2. The CLI prints the report `id`. Mention this in the response footer.

3. **If CLI fails** (Core API down): warn the user explicitly — do NOT silently fall back to file.

**Tags guideline**: Include 3-8 relevant tags per report. Used for automatic topic extraction.
Examples: `react,server-components,ssr,next.js`

## Async Slide Generation (Background Mode)

When the user asks to create slides/deck/presentation (`簡報`, `投影片`, `slides`, `pptx`):

1. Search + synthesis stay synchronous (normal flow)
2. Save the research report first (Report Output section above)
3. Start slide generation as a background job using `Bash` (`nohup ... &`)
4. Return immediately without waiting for render completion

Use this pattern:

```bash
mkdir -p ~/workshop/outputs/smart-search/jobs
nohup <deck-generation-command> \
  > ~/workshop/outputs/smart-search/jobs/<job-slug>.log 2>&1 &
echo $!
```

Response requirements for async deck requests:
- Include `Job PID`
- Include expected deck output path
- Include log path
- Include a status check command:
  `ps -p <PID> -o pid=,etime=,state=,command=`

Do not block on deck generation unless the user explicitly asks to wait.

## Response Format

Always include in the final response:

1. **Answer** — The synthesized information
2. **Sources** — Which backend(s) provided the data
3. **Quota** (if Context7 was used) — Current month usage / limit
4. **Report ID** — The database report ID (e.g., `rpt-a1b2c3d4e5f6`), or file path if fallback was used

Example footer:
```
---
Sources: DeepWiki (vercel/next.js) + Context7 (Next.js docs v15)
Context7 quota: 43/1000 (February 2026)
Report ID: rpt-a1b2c3d4e5f6
```

## Quota Management Commands

```bash
~/.local/bin/python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py status
```

## Important Notes

- **DeepWiki first** — free and unlimited, always try it before spending Context7 quota
- Context7 is the **precision tool** — save it for when DeepWiki's answer isn't enough
- Context7 quota exhausted → **DeepWiki fallback** (not Perplexity)
- Perplexity Pro membership — check `references/search-strategy.md` § Account Status for expiry date
- Context7 limit resets on the 1st of each month automatically
- If Perplexity search fails, check browser agent error output for diagnostics

## Continuous Improvement

This skill evolves with each use. After every invocation:

1. **Reflect** — Identify what worked, what caused friction, and any unexpected issues
2. **Record** — Append a concise lesson to `lessons.md` in this skill's directory
3. **Refine** — When a pattern recurs (2+ times), update SKILL.md directly

### lessons.md Entry Format

```
### YYYY-MM-DD — Brief title
- **Friction**: What went wrong or was suboptimal
- **Fix**: How it was resolved
- **Rule**: Generalizable takeaway for future invocations
```

Accumulated lessons signal when to run `/skill-optimizer` for a deeper structural review.

## Additional Resources

### Reference Files
- **`references/search-strategy.md`** — Freshness benchmarks, tool capabilities, search tips, ambiguous name examples, and quota management details

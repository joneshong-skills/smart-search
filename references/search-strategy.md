# Smart Search Strategy Reference

## Freshness Comparison (Verified 2026/02/11)

| Library | Context7 UPDATE | DeepWiki Last Indexed |
|---------|----------------|---------------------|
| Next.js | 1 day ago | 2026/01/18 (24 days) |
| Vercel AI SDK | 4 days ago | — |
| Shadcn UI | 2 days ago | — |
| Claude Code | 6 days ago | — |
| Tailwind CSS | 3 days ago | — |
| React | 5 days ago | — |

**Conclusion**: Context7 indexes every 1-5 days. DeepWiki indexes every 2-4 weeks.
For latest API details, Context7 is significantly fresher.

## Decision Tree

```
Query received
│
├─ Step 0: GitHub Code Detection (Auto-Detect for ambiguous queries)
│  │
│  ├─ SKIP if: query has clear code signals (import, API, hook, config, repo, GitHub, owner/repo)
│  ├─ SKIP if: query is clearly non-code (news, 今天, 新聞, 比較, 推薦, etc.)
│  │
│  ├─ TRIGGER if: query subject is ambiguous (name could be code or non-code)
│  │   │
│  │   └─ WebSearch: "{subject}" github
│  │       │
│  │       ├─ GitHub repo found in top results → GitHub Code Query → Route A
│  │       └─ No GitHub repo found → proceed to normal classification (Step 1)
│  │
│  Examples:
│  │  "Apollo 怎麼用"   → WebSearch "Apollo github" → apollographql → Route A
│  │  "Apollo 登月計畫"  → WebSearch "Apollo github" → NASA/history  → Step 1 (not code)
│  │  "React useEffect" → SKIP Step 0 (clear code signal) → Step 1 directly
│
├─ Step 1: Query type classification
│  │
│  ├─ [A] GitHub Code Query (Step 0 detected, or explicit code signals)
│  │   e.g. "Apollo 怎麼用" (Step 0 → GitHub match), "how does X repo work"
│  │   │
│  │   └─────→ DeepWiki + Perplexity (PARALLEL)
│  │           Run both via Task tool in parallel, synthesize results
│  │           DeepWiki: ask_question with owner/repo
│  │           Perplexity: search for broader context, examples, community usage
│  │
│  ├─ [B] Library/Framework documentation (well-known, no ambiguity)
│  │   e.g. "React useEffect", "Next.js routing", "Tailwind config"
│  │   │
│  │   ├─ Step 1: DeepWiki (FREE, unlimited)
│  │   │   └─ Determine owner/repo → ask_question
│  │   │   │
│  │   │   ├─ Answer complete & accurate → Return directly (save Context7 quota)
│  │   │   │
│  │   │   └─ Answer imprecise / missing details / needs latest API
│  │   │       │
│  │   │       ├─ Step 2: Context7 (PRECISE, 1000/month)
│  │   │       │   └─ Check quota → resolve-library-id → query-docs → increment
│  │   │       │
│  │   │       └─ Context7 quota exhausted?
│  │   │           │
│  │   │           └─ Step 3: Perplexity (FALLBACK)
│  │   │               Search: "{library} {query} documentation latest"
│  │   │
│  │   NOTE: Do NOT skip DeepWiki. Always try it first to save quota.
│  │
│  ├─ [C] Current events / news / trending
│  │   e.g. "今天新聞", "latest AI news", "recent updates"
│  │   │
│  │   └─────→ Perplexity (via Playwright)
│  │           Real-time data, Pro search capabilities
│  │
│  ├─ [D] General technical research
│  │   e.g. "best practices for X", "comparison of A vs B"
│  │   │
│  │   └─────→ Perplexity (via Playwright)
│  │           Broad knowledge, synthesized answers with sources
│  │
│  └─ [E] Hybrid / Complex query
│      e.g. "migrate from library A to B with latest patterns"
│      │
│      ├─ Step 1: DeepWiki (if involves specific repos)
│      ├─ Step 2: Context7 (only if DeepWiki insufficient, quota permitting)
│      └─ Step 3: Perplexity (for broader context / latest info)
│
└─ Return synthesized answer with source attribution
```

## Tool Capabilities

### Context7 (MCP: context7)
- **Best for**: Specific library/framework API docs and code examples
- **Strengths**: Version-accurate, code-focused, structured responses
- **Limit**: 1000 calls/month (free tier)
- **Workflow**: resolve-library-id → query-docs
- **Cost**: 1 API call = 1 resolve + 1 query (count as 1 for tracking)

### DeepWiki (MCP: deepwiki)
- **Best for**: GitHub repository documentation, architecture, code understanding
- **Strengths**: AI-powered repo analysis, no usage limits
- **Workflow**: read_wiki_structure → ask_question OR read_wiki_contents
- **Cost**: Free, unlimited

### Perplexity (via Playwright MCP)
- **Best for**: Current events, broad research, latest information
- **Strengths**: Real-time web search, synthesized answers, Pro features (until 2026/12/28)
- **Workflow**: navigate → type query → wait → extract snapshot
- **Cost**: Free with Pro membership
- **Note**: Perplexity Pro membership expires 2026/12/28

## Perplexity Search Workflow

### Standard Search
```
1. browser_navigate → https://www.perplexity.ai/
2. browser_snapshot → find search box ref
3. browser_type → ref=<search-box>, text=<query>, submit=true
4. browser_wait_for → time=10-15 (wait for response)
5. browser_snapshot → extract answer from accessibility tree
6. (Optional) browser_take_screenshot → visual capture
```

### Tips for Better Results
- Add date context for time-sensitive queries: "2026 latest..."
- Use Chinese for Taiwan-specific queries
- Use English for technical/programming queries
- Perplexity Pro supports focus modes: check if "研究" button is available for deep research

## Query Classification Keywords

### Step 0 — GitHub Detection Signals
**Clear code signals** (SKIP Step 0, go straight to classification):
import, install, API, hook, component, config, setup, npm, pip, cargo,
repo, repository, GitHub, owner/repo format, codebase, architecture, source code

**Clear non-code signals** (SKIP Step 0, classify as C/D):
today, latest, news, 今天, 最新, 新聞, 比較, 推薦, tutorial, best practice, vs

**Ambiguous** (TRIGGER Step 0 WebSearch):
A proper noun or product name without clear code/non-code context.
Examples: "Apollo", "Prisma", "Remix", "Fiber", "Echo", "Gin", "Viper"

### Type A — GitHub Code Query (Step 0 match OR explicit code signals)
Keywords: import, install, API, hook, component, config, setup, npm, pip, cargo,
repo, repository, codebase, architecture, source code, implementation,
how does X work (referring to a specific project), contribute,
+ any query where Step 0 found a GitHub repo
Backend: **DeepWiki + Perplexity (parallel)**

### Type B — Library/Framework Docs (well-known, no ambiguity)
Keywords: import, install, API, hook, component, config, setup, usage, example,
migration, version, typescript, props, method, function, class
Backend: **DeepWiki first** → Context7 supplement

### Type C — Current Events
Keywords: today, latest, news, trending, 今天, 最新, 新聞, recent, update,
this week, this month, 2026

### Type D — General Research
Keywords: best practice, comparison, vs, alternative, recommend, pros cons,
how to, tutorial, guide, 比較, 推薦, 教學

### Type E — Hybrid
Multiple keyword categories detected, or explicit multi-source request

> **Note**: Types [A-E] are *classification categories*. SKILL.md's Routes [A-E] are
> *execution paths*. They largely align, but Route C (Context7) is a sub-route of
> Route B (escalation when DeepWiki is insufficient), not a standalone classification.

## Usage Tracking

### Tracker Script
Location: `~/.claude/skills/smart-search/scripts/usage_tracker.py`

```bash
# Check current status
python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py status

# Record a Context7 call
python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py increment

# Check if quota available (exit code 0=yes, 1=no)
python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py check
```

### Auto-Switch Rules
- count < threshold (900): Context7 available, but still try DeepWiki first
- count >= threshold (900): WARNING — mention remaining quota, strongly prefer DeepWiki
- count >= limit (1000): EXHAUSTED — all library queries routed to DeepWiki, then Perplexity if needed

### Data File
Location: `~/.claude/skills/smart-search/data/usage.json`
```json
{
  "month": "2026-02",
  "count": 42,
  "limit": 1000,
  "threshold": 900,
  "history": {
    "2026-01": 876
  }
}
```

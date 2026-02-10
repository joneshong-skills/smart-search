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
├─ Query type classification
│  │
│  ├─ [A] Library/Framework documentation
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
│  ├─ [B] GitHub repository question
│  │   e.g. "how does X repo work", "architecture of Y project"
│  │   │
│  │   └─────→ DeepWiki (read_wiki_structure → ask_question)
│  │           Free, unlimited, always preferred for repo questions
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

### Perplexity (via Playwright MCP + Browser Tools MCP)
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

### Type A — Library Docs
Keywords: import, install, API, hook, component, config, setup, usage, example,
migration, version, typescript, props, method, function, class

### Type B — Repo Questions
Keywords: repo, repository, codebase, architecture, source code, implementation,
how does X work (referring to a specific project), contribute

### Type C — Current Events
Keywords: today, latest, news, trending, 今天, 最新, 新聞, recent, update,
this week, this month, 2026

### Type D — General Research
Keywords: best practice, comparison, vs, alternative, recommend, pros cons,
how to, tutorial, guide, 比較, 推薦, 教學

### Type E — Hybrid
Multiple keyword categories detected, or explicit multi-source request

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

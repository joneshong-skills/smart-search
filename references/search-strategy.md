# Smart Search Strategy Reference

Supplementary data for the smart-search skill. For the core decision tree and routes,
see SKILL.md. This file contains freshness benchmarks, tool capabilities, search tips,
and quota management details.

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
- **Strengths**: Real-time web search, synthesized answers, Pro features (see § Account Status)
- **Workflow**: navigate → type query → wait → extract snapshot
- **Cost**: Free with Pro membership

## Perplexity Search Tips

- Add date context for time-sensitive queries: "2026 latest..."
- Use Chinese for Taiwan-specific queries
- Use English for technical/programming queries
- Perplexity Pro supports focus modes: check if "研究" button is available for deep research

## Query Classification — Ambiguous Name Examples

When Step 0 (GitHub Detection) triggers, here are common ambiguous names and their resolutions:

| Name | Code? | Repo | Non-code meaning |
|------|-------|------|-----------------|
| Apollo | Yes | apollographql/apollo-client | NASA space program |
| Prisma | Yes | prisma/prisma | Optical prism |
| Remix | Yes | remix-run/remix | Music remix |
| Fiber | Yes | gofiber/fiber | Textile fiber |
| Echo | Yes | labstack/echo | Sound echo |
| Gin | Yes | gin-gonic/gin | Alcoholic drink |
| Viper | Yes | spf13/viper | Snake species |

## Quota Auto-Switch Rules

| Condition | Behavior |
|-----------|----------|
| count < 900 | Context7 available; still try DeepWiki first |
| count >= 900 | WARNING — mention remaining quota, strongly prefer DeepWiki |
| count >= 1000 | EXHAUSTED — all library queries → DeepWiki, then Perplexity |

## Data File Schema

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

- `month`: Auto-resets when current month differs from stored month
- `count`: Incremented by `usage_tracker.py increment`
- `history`: Previous months' counts preserved on reset

## Account Status

> **Update this section** whenever a subscription is renewed, cancelled, or changed.

| Service | Plan | Expires | Notes |
|---------|------|---------|-------|
| Perplexity | Pro | 2026/12/28 | Annual subscription; update date on renewal |

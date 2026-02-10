[English](README.md) | [繁體中文](README.zh.md)

# Smart Search

A Claude Code skill that intelligently routes search queries across multiple backends — **DeepWiki**, **Context7**, and **Perplexity Pro** — to deliver the best answer with minimal cost.

## What It Does

Smart Search automatically selects the optimal search backend based on your query type:

| Query Type | Primary Backend | Fallback |
|---|---|---|
| Library / framework docs | DeepWiki (free, unlimited) | Context7 (precise, 1000/month) |
| GitHub repo architecture | DeepWiki | — |
| Current events & news | Perplexity Pro | — |
| General research & comparisons | Perplexity Pro | — |
| Hybrid / multi-source | Parallel combination | — |

**Key design principle:** DeepWiki is always tried first for library questions (free and unlimited). Context7 is reserved as a precision supplement for exact API signatures and latest syntax. Perplexity handles current events and serves as the final fallback.

### Quota Management

Context7 has a 1,000 calls/month limit. The skill tracks usage automatically and falls back to DeepWiki when the quota is exhausted — never wasting calls unnecessarily.

## Installation

1. Copy or clone this repository into your Claude skills directory:

   ```bash
   git clone https://github.com/joneshong-skills/smart-search.git ~/.claude/skills/smart-search
   ```

2. Ensure the required MCP servers are available in your Claude Code environment:
   - `deepwiki` — for free, unlimited library/repo documentation queries
   - `context7` — for precise, version-specific API documentation
   - `playwright` — for Perplexity Pro web searches

3. The skill activates automatically when you ask Claude to search, look up documentation, research a topic, or use trigger phrases like "search for", "look up", "find the latest", etc.

## Usage

Just ask Claude naturally. Examples:

- *"Search for the Next.js App Router migration guide"*
- *"Look up the latest React Server Components API"*
- *"Find the latest news on TypeScript 6.0"*
- *"Research best practices for database connection pooling"*

### Check Context7 Quota

```bash
python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py status
```

## Project Structure

```
smart-search/
├── SKILL.md                        # Skill definition and routing logic
├── README.md                       # This file
├── data/
│   └── usage.json                  # Context7 monthly usage tracker
├── references/
│   └── search-strategy.md          # Detailed decision tree and workflow docs
└── scripts/
    └── usage_tracker.py            # Context7 quota tracking script
```

## License

MIT

# Route F: Deep Research Pipeline (Antigravity CLI + Codex CLI)

**Triggered when**: Step 1.5 classifies depth as `deep` or `research`.

This route leverages each CLI's unique strength:
- **Antigravity CLI**: Google Search grounding (largest web index, 45% citation rate)
- **Codex CLI**: o3 reasoning-native model (deep chain-of-thought analysis)
- **Claude**: Final synthesis with context management

## Phase 1: Parallel Search (both `deep` and `research`)

Launch **all legs simultaneously** using parallel agent calls:

### Leg 1: Antigravity CLI search (Task, subagent_type: worker)

```
Prompt: Use Bash to run Antigravity CLI for web search. Execute:

script -q /dev/null agy -p "Search the web thoroughly for the following query. Find 5-10 authoritative sources with diverse perspectives. For each source, provide: URL, key findings, and a relevance rating (1-5).

Query: {query}

Output format:
## Source 1
- URL: ...
- Key findings: ...
- Relevance: X/5

(repeat for each source)" -m gemini-2.5-flash 2>&1 | head -500

Return the COMPLETE Gemini output. Do not summarize.
```

### Leg 2: WebSearch (inline in main context)

Standard WebSearch + WebFetch flow (existing behavior).

### Leg 3: DeepWiki (Task, subagent_type: general-purpose, IF query is code/library related)

Standard DeepWiki query via MCP tools.

Wait for all parallel legs to complete before proceeding.

## Phase 2: Codex Deep Analysis (`research` depth only)

After Phase 1 results are collected, feed them to Codex for deep reasoning.
Skip this phase for `deep` depth — go directly to Claude synthesis.

**Codex analysis agent** (Task, subagent_type: worker):
```
Prompt: Use Bash to run Codex CLI for deep analysis. First write the search results
to a temp file, then run Codex:

cat << 'SEARCH_EOF' > /tmp/smart-search-input.md
{combined Phase 1 results from all legs}
SEARCH_EOF

script -q /dev/null codex exec --skip-git-repo-check --sandbox read-only \
  "Read /tmp/smart-search-input.md which contains raw search results about: {query}

Perform deep analysis:
1. Cross-validate claims — flag what appears in 2+ sources vs single-source claims
2. Identify contradictions between sources and assess which is more credible
3. Fill gaps — what important aspects are NOT covered by the search results?
4. Rate overall confidence (high/medium/low) for each key finding
5. Synthesize 3-5 actionable insights with evidence chains

Output a structured markdown report with sections:
## Key Findings (ranked by confidence)
## Contradictions & Gaps
## Actionable Insights
## Confidence Assessment" 2>&1 | head -800

Return the COMPLETE Codex output. Do not summarize.
```

Clean up: `rm -f /tmp/smart-search-input.md`

## Phase 3: Claude Synthesis (always)

Claude (main context) synthesizes:
- For `deep`: Merge Gemini + WebSearch + DeepWiki results using Judge Agent pattern
- For `research`: Integrate Codex analysis as the primary analytical backbone,
  supplemented by raw search results for any details Codex missed

**Important**: In the response, clearly attribute which insights came from which source
(Gemini Search, WebSearch, DeepWiki, Codex Analysis).

## Fallback Handling

- **Antigravity CLI unavailable** (not installed, hangs >60s, or errors): Fall back to
  WebSearch-only for that leg. Log: "Antigravity CLI unavailable, fell back to WebSearch"
- **Codex CLI unavailable**: Fall back to Claude-only synthesis (skip Phase 2).
  Log: "Codex CLI unavailable, Claude performing direct synthesis"
- **Both unavailable**: Degrade gracefully to existing Route D (WebSearch only)

## Example Flow

```
User: "深度研究 React Server Components vs Astro Islands 的效能差異"

Step 1: Classify → General research (comparison)
Step 1.5: Depth → research (user said "深度研究")

Route F activated:
  Phase 1 (parallel, ~30s):
    ├─ Antigravity CLI: Google Search for RSC vs Astro benchmarks
    ├─ WebSearch: Supplementary web results
    └─ DeepWiki: facebook/react + withastro/astro (code-related)

  Phase 2 (sequential, ~30-60s):
    └─ Codex CLI: Deep analysis of combined Phase 1 results

  Phase 3: Claude synthesizes final report
```

#!/usr/bin/env python3
"""Smart-search route registry — programmatic replacement for SKILL.md classification table.

Provides a structured, testable registry of Routes A-F with keyword-based classification.
Integrates with usage_tracker.py for Context7 quota awareness.

Data source: ~/.claude/skills/smart-search/SKILL.md (CLASSIFY / DEPTH_CHECK sections)

Usage:
    python3 route_registry.py classify "query text"                        # JSON output
    python3 route_registry.py classify "query" --context '{"depth":"deep"}'
    python3 route_registry.py list                                          # all routes
    python3 route_registry.py list --available                              # only enabled
    python3 route_registry.py prompt "ambiguous query"                     # LLM classification prompt
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
USAGE_TRACKER = SCRIPTS_DIR / "usage_tracker.py"

# Confidence threshold below which LLM assistance is recommended
LLM_THRESHOLD = 0.4

# GitHub owner/repo pattern: word/word, excluding obvious URLs
_GITHUB_REPO_RE = re.compile(r"\b[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\b")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Route:
    """A single named search route with classification metadata."""

    id: str
    """Single-letter identifier: A, B, C, D, E, F."""

    name: str
    """Human-readable route name."""

    triggers: list[str]
    """Keyword/phrase signals that indicate this route (English + Chinese)."""

    backends: list[str]
    """Backend tools used: deepwiki, websearch, context7, antigravity-cli, codex-cli."""

    cost_tier: str
    """Cost category: 'free' | 'quota' | 'expensive'."""

    priority: int
    """Tie-breaking priority; lower value = preferred over higher value."""

    depth_levels: list[str]
    """Which depth modes this route supports: 'normal', 'deep', 'research'."""

    query_types: list[str]
    """Abstract query categories this route handles (e.g. 'github-code', 'library-docs')."""

    description: str = ""
    """Short prose description of when to use this route."""

    enabled: bool = True
    """Whether this route is currently active."""


@dataclass
class ClassifyResult:
    """Output of RouteRegistry.classify()."""

    route: Route
    """Best matching route."""

    confidence: float
    """Match confidence in [0.0, 1.0]. Below LLM_THRESHOLD → needs_llm=True."""

    matched_triggers: list[str]
    """Which trigger keywords contributed to this result."""

    needs_llm: bool
    """True when confidence is too low for reliable keyword-only classification."""

    depth: str = "normal"
    """Resolved depth: 'normal' | 'deep' | 'research'."""

    context7_available: bool = True
    """Snapshot of Context7 quota availability (Route C relevance)."""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class RouteRegistry:
    """Registry of search routes with keyword-based classification.

    Typical use:
        registry = RouteRegistry.default()
        result = registry.classify("how to use React hooks")
        print(result.route.id)   # "B"
    """

    def __init__(self) -> None:
        self._routes: dict[str, Route] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, route: Route) -> None:
        """Add a route to the registry, replacing any existing route with the same id."""
        self._routes[route.id] = route

    def unregister(self, route_id: str) -> None:
        """Remove a route by id. Silently ignores missing ids."""
        self._routes.pop(route_id, None)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_available(self, context: dict | None = None) -> list[Route]:
        """Return enabled routes, optionally filtered by depth from context.

        Args:
            context: Optional dict with keys such as ``{"depth": "deep"}``.

        Returns:
            Sorted list of enabled Route objects (by priority).
        """
        depth = (context or {}).get("depth", "normal")
        routes = [r for r in self._routes.values() if r.enabled]
        if depth != "normal":
            routes = [r for r in routes if depth in r.depth_levels]
        return sorted(routes, key=lambda r: r.priority)

    def all_routes(self) -> list[Route]:
        """Return all registered routes sorted by priority."""
        return sorted(self._routes.values(), key=lambda r: r.priority)

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify(self, query: str, context: dict | None = None) -> ClassifyResult:
        """Classify a query into the best matching route.

        Algorithm:
        1. Normalize query (lowercase).
        2. GitHub auto-detect: owner/repo pattern → Route A, high confidence.
        3. Score each enabled route by trigger keyword overlap.
        4. Resolve depth from context + depth trigger keywords.
        5. If top route doesn't support resolved depth, fall back to Route F.
        6. If confidence < LLM_THRESHOLD, set needs_llm=True.
        7. Fallback to Route D if no match.

        Args:
            query:   Raw user query string.
            context: Optional dict. Supported keys:
                     - ``depth``: 'normal' | 'deep' | 'research' (overrides auto-detect)

        Returns:
            ClassifyResult with the best matching route.
        """
        ctx = context or {}
        normalized = query.lower()

        # Step 1: GitHub auto-detect (owner/repo pattern)
        if self._is_github_query(normalized):
            route = self._routes.get("A")
            if route and route.enabled:
                depth = self._resolve_depth(normalized, ctx)
                c7_ok = self._check_context7_quota()
                return ClassifyResult(
                    route=route,
                    confidence=0.9,
                    matched_triggers=["owner/repo pattern"],
                    needs_llm=False,
                    depth=depth,
                    context7_available=c7_ok,
                )

        # Step 2: Score all enabled routes
        scores: dict[str, tuple[float, list[str]]] = {}
        for route in self._routes.values():
            if not route.enabled:
                continue
            score, matched = self._score_route(normalized, route)
            scores[route.id] = (score, matched)

        # Step 3: Resolve depth
        depth = self._resolve_depth(normalized, ctx)

        # Step 4: Pick best route; must support resolved depth
        best_id, best_score, best_triggers = self._pick_best(scores, depth)

        # Step 5: Context7 quota check (affects Route C availability)
        c7_ok = self._check_context7_quota()
        if not c7_ok and best_id == "C":
            # Downgrade to Route B when Context7 quota is exhausted
            fallback = self._routes.get("B")
            if fallback and fallback.enabled:
                b_score, b_triggers = scores.get("B", (0.0, []))
                best_id = "B"
                best_score = b_score
                best_triggers = b_triggers

        route = self._routes.get(best_id) or self._routes.get("D")
        needs_llm = best_score < LLM_THRESHOLD

        return ClassifyResult(
            route=route,  # type: ignore[arg-type]
            confidence=best_score,
            matched_triggers=best_triggers,
            needs_llm=needs_llm,
            depth=depth,
            context7_available=c7_ok,
        )

    def get_classification_prompt(self, query: str) -> str:
        """Generate an LLM-ready classification prompt for ambiguous queries.

        Returns a self-contained prompt string that can be sent to any LLM.
        The expected response format is a JSON object with keys: route_id, confidence, reason.

        Args:
            query: The ambiguous query that needs LLM assistance.
        """
        routes_summary = "\n".join(
            f"  {r.id}: {r.name} — {r.description}" for r in self.all_routes() if r.enabled
        )
        return (
            f"You are a search-route classifier. Given the user query below, "
            f"select the best route from the options and respond ONLY with valid JSON.\n\n"
            f"Routes:\n{routes_summary}\n\n"
            f'Query: """{query}"""\n\n'
            f"Respond with: "
            f'{{"route_id": "<A|B|C|D|E|F>", "confidence": <0.0-1.0>, "reason": "<one sentence>"}}'
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_github_query(normalized: str) -> bool:
        """Return True if the query contains a GitHub owner/repo pattern."""
        if _GITHUB_REPO_RE.search(normalized):
            # Exclude HTTP URLs which naturally contain slashes
            if "http" not in normalized and "www." not in normalized:
                return True
        github_signals = ("github.com/", " github ", "github repo")
        return any(sig in normalized for sig in github_signals)

    @staticmethod
    def _score_route(normalized: str, route: Route) -> tuple[float, list[str]]:
        """Score a single route against the normalized query.

        Scoring:
        - Exact substring match of trigger phrase: +1.0 per match
        - Partial word-boundary match (single keyword in phrase): +0.5
        - Score is normalized by total trigger count to produce [0, 1].
        """
        matched: list[str] = []
        raw_score = 0.0

        for trigger in route.triggers:
            trigger_lower = trigger.lower()
            if trigger_lower in normalized:
                matched.append(trigger)
                raw_score += 1.0
            else:
                # Check individual words in multi-word trigger
                words = trigger_lower.split()
                if len(words) > 1:
                    if any(w in normalized for w in words if len(w) > 2):
                        matched.append(f"~{trigger}")
                        raw_score += 0.5

        if not route.triggers:
            return 0.0, []

        confidence = min(raw_score / len(route.triggers), 1.0)
        # Bonus for multiple distinct matches
        if len(matched) >= 3:
            confidence = min(confidence + 0.1, 1.0)
        return confidence, matched

    def _resolve_depth(self, normalized: str, ctx: dict) -> str:
        """Determine search depth from explicit context or trigger keywords."""
        if "depth" in ctx:
            return ctx["depth"]

        research_triggers = {"深度研究", "research report", "competitive", "company-intel"}
        deep_triggers = {
            "深度搜尋",
            "深度",
            "驗證",
            "verify",
            "deep search",
            "cross-reference",
            "全面比較",
        }

        for t in research_triggers:
            if t in normalized:
                return "research"
        for t in deep_triggers:
            if t in normalized:
                return "deep"
        return "normal"

    def _pick_best(
        self, scores: dict[str, tuple[float, list[str]]], depth: str
    ) -> tuple[str, float, list[str]]:
        """Return (route_id, confidence, matched_triggers) for the best scoring route.

        Prefers routes that support the resolved depth. Falls back to Route D.
        """
        # Filter to routes that support the depth
        depth_filtered = {
            rid: (score, triggers)
            for rid, (score, triggers) in scores.items()
            if depth in (self._routes[rid].depth_levels)
        }

        candidate_pool = depth_filtered if depth_filtered else scores

        if not candidate_pool:
            return "D", 0.0, []

        # Sort by score desc, then priority asc
        best_id = max(
            candidate_pool,
            key=lambda rid: (
                candidate_pool[rid][0],
                -self._routes[rid].priority,
            ),
        )
        best_score, best_triggers = candidate_pool[best_id]

        # If best score is 0, fall back to Route D
        if best_score == 0.0:
            return "D", 0.0, []

        return best_id, best_score, best_triggers

    @staticmethod
    def _check_context7_quota() -> bool:
        """Return True if Context7 quota is available, via usage_tracker.py check.

        Falls back to True if usage_tracker.py is unavailable (non-critical).
        """
        if not USAGE_TRACKER.exists():
            return True
        try:
            result = subprocess.run(
                [sys.executable, str(USAGE_TRACKER), "check"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return True

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> RouteRegistry:
        """Create a RouteRegistry pre-populated with Routes A-F from SKILL.md."""
        registry = cls()

        registry.register(
            Route(
                id="A",
                name="DeepWiki + WebSearch (GitHub Code)",
                triggers=[
                    # English
                    "github",
                    "repo",
                    "repository",
                    "import",
                    "architecture",
                    "source code",
                    "codebase",
                    "pull request",
                    "open source",
                    "package",
                    "module",
                    "library source",
                    "implementation",
                    # Pattern-based (supplemental — main detection via regex)
                    "owner/repo",
                ],
                backends=["deepwiki", "websearch"],
                cost_tier="free",
                priority=1,
                depth_levels=["normal", "deep", "research"],
                query_types=["github-code"],
                description=(
                    "Use when query targets a specific GitHub repository, open-source project, "
                    "or code architecture. DeepWiki provides repo-level understanding; "
                    "WebSearch surfaces issues, discussions and recent changes."
                ),
            )
        )

        registry.register(
            Route(
                id="B",
                name="DeepWiki → Context7 Escalation (Library Docs)",
                triggers=[
                    # English
                    "library",
                    "hook",
                    "config",
                    "configuration",
                    "api usage",
                    "documentation",
                    "docs",
                    "sdk",
                    "framework",
                    "plugin",
                    "how to use",
                    "tutorial",
                    "example",
                    "getting started",
                    # Known library names (representative sample)
                    "react",
                    "vue",
                    "angular",
                    "nextjs",
                    "nuxtjs",
                    "fastapi",
                    "pydantic",
                    "sqlalchemy",
                    "langchain",
                    "openai",
                    "anthropic",
                    "typescript",
                    "tailwind",
                    "shadcn",
                    "prisma",
                    "drizzle",
                    # Chinese
                    "用法",
                    "範例",
                    "教學",
                    "說明文件",
                    "文件",
                ],
                backends=["deepwiki", "context7"],
                cost_tier="quota",
                priority=2,
                depth_levels=["normal", "deep", "research"],
                query_types=["library-docs"],
                description=(
                    "Use for known libraries or frameworks where official documentation matters. "
                    "DeepWiki runs first for architecture overview; Context7 escalated for "
                    "version-precise API snippets if gaps remain."
                ),
            )
        )

        registry.register(
            Route(
                id="C",
                name="Context7 Precision (Version-Specific API)",
                triggers=[
                    "breaking change",
                    "migration",
                    "upgrade",
                    "v2",
                    "v3",
                    "version",
                    "changelog",
                    "deprecat",
                    "exact api",
                    "since version",
                    "new in",
                    "removed in",
                    "renamed",
                    # Chinese
                    "版本",
                    "升級",
                    "遷移",
                    "棄用",
                    "異動",
                ],
                backends=["context7"],
                cost_tier="quota",
                priority=3,
                depth_levels=["normal", "deep"],
                query_types=["version-specific-api"],
                description=(
                    "Use when the query is narrowly version-specific: exact API signature, "
                    "breaking changes between versions, or official changelog detail. "
                    "Requires Context7 quota; degrades to Route B if exhausted."
                ),
            )
        )

        registry.register(
            Route(
                id="D",
                name="WebSearch (Current Events / General Research)",
                triggers=[
                    # Time-sensitive
                    "today",
                    "latest",
                    "recent",
                    "2026",
                    "2025",
                    "this week",
                    "just released",
                    "new release",
                    "announcement",
                    # Comparison / general
                    "vs",
                    "versus",
                    "comparison",
                    "compare",
                    "alternative",
                    "best",
                    "top",
                    "recommend",
                    "tutorial",
                    "guide",
                    "how to",
                    "why",
                    "what is",
                    "explain",
                    # Chinese
                    "最新",
                    "最近",
                    "今天",
                    "比較",
                    "推薦",
                    "教程",
                    "是什麼",
                    "為什麼",
                    "怎麼",
                ],
                backends=["websearch"],
                cost_tier="free",
                priority=4,
                depth_levels=["normal", "deep", "research"],
                query_types=["current-events", "general-research", "comparison", "tutorial"],
                description=(
                    "General-purpose web search route. Handles current events, news, comparisons, "
                    "tutorials, and anything that benefits from live web results. "
                    "Also the fallback when no other route matches."
                ),
            )
        )

        registry.register(
            Route(
                id="E",
                name="Hybrid (Multiple Sources in Parallel)",
                triggers=[
                    "compare",
                    "comprehensive",
                    "full picture",
                    "overview",
                    "both",
                    "all sources",
                    "multiple",
                    "combination",
                    # Chinese
                    "全面",
                    "綜合",
                    "整體",
                    "多方",
                    "各方",
                ],
                backends=["deepwiki", "websearch", "context7"],
                cost_tier="quota",
                priority=5,
                depth_levels=["normal", "deep", "research"],
                query_types=["hybrid", "multi-source"],
                description=(
                    "Use when the query spans multiple query types (e.g. library docs + community "
                    "opinions + current events). Runs applicable sub-routes in parallel via Task tool "
                    "and synthesizes noting source origin."
                ),
            )
        )

        registry.register(
            Route(
                id="F",
                name="Deep Research Pipeline (Antigravity CLI + Codex CLI)",
                triggers=[
                    # English
                    "deep",
                    "research",
                    "verify",
                    "cross-reference",
                    "thorough",
                    "comprehensive analysis",
                    "competitive",
                    "company intel",
                    "deep dive",
                    "in-depth",
                    "exhaustive",
                    # Chinese
                    "深度",
                    "深度搜尋",
                    "深度研究",
                    "驗證",
                    "研究報告",
                    "競品",
                    "深入",
                    "全面分析",
                ],
                backends=["antigravity-cli", "websearch", "codex-cli"],
                cost_tier="expensive",
                priority=6,
                depth_levels=["deep", "research"],
                query_types=["deep-research", "competitive-intel", "verification"],
                description=(
                    "Multi-phase deep research pipeline. Phase 1: Antigravity CLI (Google Search "
                    "grounding) + WebSearch in parallel → Claude synthesis. "
                    "Phase 2 (research only): Codex CLI deep analysis. "
                    "Falls back to Route D if CLI tools unavailable."
                ),
            )
        )

        return registry


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


def cmd_classify(query: str, context_json: str | None, registry: RouteRegistry) -> None:
    """Run classification and print JSON result."""
    ctx: dict = {}
    if context_json:
        try:
            ctx = json.loads(context_json)
        except json.JSONDecodeError as exc:
            print(json.dumps({"error": f"Invalid context JSON: {exc}"}))
            sys.exit(1)

    result = registry.classify(query, ctx)
    output = {
        "route_id": result.route.id,
        "route_name": result.route.name,
        "confidence": round(result.confidence, 3),
        "matched_triggers": result.matched_triggers,
        "needs_llm": result.needs_llm,
        "depth": result.depth,
        "context7_available": result.context7_available,
        "backends": result.route.backends,
        "cost_tier": result.route.cost_tier,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_list(available_only: bool, context_json: str | None, registry: RouteRegistry) -> None:
    """Print all routes (or only available ones) as JSON."""
    ctx: dict = {}
    if context_json:
        try:
            ctx = json.loads(context_json)
        except json.JSONDecodeError as exc:
            print(json.dumps({"error": f"Invalid context JSON: {exc}"}))
            sys.exit(1)

    routes = registry.get_available(ctx) if available_only else registry.all_routes()
    output = [
        {
            "id": r.id,
            "name": r.name,
            "backends": r.backends,
            "cost_tier": r.cost_tier,
            "priority": r.priority,
            "depth_levels": r.depth_levels,
            "query_types": r.query_types,
            "description": r.description,
            "enabled": r.enabled,
            "trigger_count": len(r.triggers),
        }
        for r in routes
    ]
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_prompt(query: str, registry: RouteRegistry) -> None:
    """Print an LLM classification prompt for ambiguous queries."""
    print(registry.get_classification_prompt(query))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="route_registry.py",
        description="Smart-search route registry — classify queries to search routes A-F.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # classify
    p_classify = sub.add_parser("classify", help="Classify a query into a route (JSON output).")
    p_classify.add_argument("query", help="The search query string.")
    p_classify.add_argument(
        "--context",
        metavar="JSON",
        help='Optional JSON context, e.g. \'{"depth": "deep"}\'.',
    )

    # list
    p_list = sub.add_parser("list", help="List all registered routes.")
    p_list.add_argument(
        "--available",
        action="store_true",
        help="Show only enabled routes.",
    )
    p_list.add_argument(
        "--context",
        metavar="JSON",
        help="Optional JSON context to filter by depth when --available is set.",
    )

    # prompt
    p_prompt = sub.add_parser(
        "prompt",
        help="Generate an LLM classification prompt for an ambiguous query.",
    )
    p_prompt.add_argument("query", help="The ambiguous query string.")

    return parser


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()
    registry = RouteRegistry.default()

    if args.command == "classify":
        cmd_classify(args.query, getattr(args, "context", None), registry)
    elif args.command == "list":
        cmd_list(args.available, getattr(args, "context", None), registry)
    elif args.command == "prompt":
        cmd_prompt(args.query, registry)
    else:
        parser.print_help()
        sys.exit(1)

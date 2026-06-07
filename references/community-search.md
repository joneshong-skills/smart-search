# Community/Forum Search — 9 Platform Strategy

When the query involves community opinions, user experiences, or discussion-based questions,
search these 9 platforms using WebSearch + WebFetch.

## Global Search Priority Order

Always follow this sequence:

1. Reddit
2. X (Twitter)
3. 知乎 (Zhihu)
4. CSDN
5. Facebook
6. Threads
7. 小紅書 (Xiaohongshu)
8. PTT
9. Stack Overflow

**Region grouping** (for reference only):
- Western: Reddit, X, Stack Overflow
- China: 知乎, CSDN, 小紅書
- Taiwan: Facebook, Threads, PTT

## Execution

Run WebSearch queries following the priority order above, using
`site:reddit.com`, `site:zhihu.com`, `site:ptt.cc` etc. as site filters.
Parallelize where possible but present results in priority order.
If a platform is clearly irrelevant to the query topic, skip it.

## Phase 2: Entity Drill-Down

When depth warrants it, after Phase 1 results come back, extract high-signal entities:
- Reddit: active subreddits (r/...) and top posters (u/...)
- X: influential @handles with high engagement
- Other: recurring author names or sources

Then run targeted follow-up searches:
- `"topic" site:reddit.com/r/{subreddit}` for the most relevant subreddit
- `"topic" from:@handle site:x.com` for top voices

This two-phase approach surfaces deeper, higher-quality results
that broad searches miss. Skip Phase 2 for quick/simple queries.

## Trend Scan — Time-Filtered Community Search

When the query asks about **trends, what's working, or recent community sentiment**
(keywords: 趨勢, trending, last N days, 這個月, 最近在討論, what's working),
use Community Search with time filters.

**Time range detection**:
- Explicit: "last 7 days", "這週", "past month" → use stated range
- Implicit: "最近", "trending", "what's working now" → default to **30 days**

**Execution**: Append time operators to WebSearch queries:
```
"{topic} site:reddit.com" after:2026-01-27   ← (30 days ago)
"{topic} site:x.com" after:2026-02-20        ← (last 7 days)
```

**Output structure for trend scans**:
1. **Top themes** — What patterns emerge across platforms?
2. **Notable discussions** — Link to 3-5 highest-signal threads
3. **Consensus vs debate** — Where do people agree? Where do they disagree?
4. **Actionable takeaways** — What can the user do based on this?

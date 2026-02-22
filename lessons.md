### 2026-02-15 — Async deck generation by default
- **Friction**: Slide/deck generation blocked the main response flow and increased user wait time.
- **Fix**: Added background-mode (`nohup ... &`) rule with PID/log/output-path reporting.
- **Rule**: For presentation requests, finish research synchronously, then run deck generation asynchronously unless user asks to wait.

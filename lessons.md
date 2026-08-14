### 2026-02-15 — Async deck generation by default
- **Friction**: Slide/deck generation blocked the main response flow and increased user wait time.
- **Fix**: Added background-mode (`nohup ... &`) rule with PID/log/output-path reporting.
- **Rule**: For presentation requests, finish research synchronously, then run deck generation asynchronously unless user asks to wait.

### 2026-02-22 — browser agent cannot access Playwright MCP tools
- **Friction**: Perplexity searches silently fell back to WebSearch since ~2/11. `browser` agent has `Tools: Bash, Read, Write` only — no ToolSearch, so it cannot load deferred Playwright MCP tools. The SKILL.md fallback "if Playwright is unavailable" triggered every time.
- **Fix**: Changed Perplexity delegation from `browser` to `general-purpose` agent (has `Tools: *` including ToolSearch). Added explicit ToolSearch step in Route A/D instructions.
- **Rule**: Any sub-agent needing MCP tools must have `ToolSearch` access. Only `general-purpose` (`Tools: *`) has this. Never delegate MCP-dependent work to specialized agents (`browser`, `researcher`, etc.). This includes ALL MCP tools: Playwright, DeepWiki, Context7, etc.

### 2026-02-25 — GitNexus Next-Step Hints pattern adopted
- **Friction**: After MCP tool calls, AI agents sometimes lost track of optimal next actions, leading to unnecessary queries or hallucinated steps.
- **Fix**: Implemented `hints.ts` module in both `sandbox-executor` (2 tools) and `kas-memory` (9 tools) MCP servers. Each tool response now appends a contextual `💡 Next:` hint based on tool name + result state (success/failure/empty).
- **Rule**: When building MCP tools, always include a next-step hint in tool responses. This is a low-cost, high-impact pattern that replaces complex coordinator agents with simple self-guiding workflows.

### 2026-03-01 — MCP audit: Playwright MCP removed, WebSearch+WebFetch as primary
- **Friction**: Playwright MCP × 2 cost ~7,200 tokens schema per session. Perplexity-via-Playwright was fragile (browser agent ToolSearch issue from 2/22, page load failures). The entire Perplexity route was a complex 6-step MCP chain for what WebSearch does natively.
- **Fix**: Removed both Playwright MCP servers. All search routes (A/D/E) now use WebSearch+WebFetch inline. Playwright CLI (`@playwright/mcp`) preserved for rare browser automation needs via Bash, with dynamic session profiles synced from master.
- **Rule**: For search skills, prefer built-in tools (WebSearch+WebFetch) over MCP-dependent browser automation chains. MCP servers are justified only when they provide capabilities not available through simpler tools. The 68 vs 3,600 token difference per task is decisive.

### 2026-03-04 — FSM refactor: SKILL.md 555→247 lines
- **Friction**: Deep Research Pipeline (Route F) 新增後 SKILL.md 膨脹至 555 行，超過 500 行上限。線性流程敘述難以一眼看清控制流。
- **Fix**: 用 FSM 狀態圖（PRE_CHECK → CLASSIFY → DEPTH_CHECK → EXECUTE → SYNTHESIZE → REPORT_SAVE）取代線性敘述。253 行執行細節抽至 3 個 `references/` 檔案（community-search, deep-research-pipeline, report-io）。SKILL.md 只保留狀態轉移 + 每個 Route 一句話摘要。
- **Rule**: 當 Skill 流程有 3+ 分支（條件判斷）時，用 FSM 狀態圖取代線性敘述，詳細執行步驟抽至 `references/`。SKILL.md = 決策樹 + 指針，references = 執行手冊。

### 2026-02-27 — last30days-skill analysis: 3 patterns adopted
- **Friction**: Community Search returned flat WebSearch results with no engagement weighting, no entity drill-down, and synthesis was basic concatenation.
- **Fix**: Added 3 patterns to SKILL.md v0.4.0:
  1. **Phase 2 Entity Drill-Down** — extract @handles/r/subreddits from Phase 1, run targeted follow-up searches
  2. **Judge Agent Synthesis** — cross-source verification with engagement weighting and contradiction flagging
  3. **feedscan integration note** — future Core Module will replace raw WebSearch with normalized, scored results
- **Rule**: For community/trend queries, always do two-phase search (broad → entity → targeted) and synthesize with cross-validation, not concatenation. Engagement signals (upvotes, likes) should weight result priority.

### 2026-03-30 — Report API endpoint drift: 8830 → 10000/intelflow, raw curl → SDK
- **Friction**: SKILL.md still referenced old `localhost:8830/api/research/*` endpoints. The intelflow module lives on Core API (port 10000) at `/api/intelflow/*`. Raw curl also lacked `X-Internal-Key` auth header, causing 401 "Not authenticated". Report silently fell back to local file write, never reaching the DB.
- **Fix**: Replaced all curl commands with `sdk_client.intelflow.IntelflowClient` calls. SDK handles auth (`X-Internal-Key` via `CORE_INTERNAL_API_KEY` env), `space_id`, and error handling automatically. Also fixed `sources` field from `list[str]` to `list[dict]`.
- **Rule**: Never use raw curl for Core API calls in skills — always use `sdk_client.*Client`. The SDK handles auth, space_id, and error wrapping. When an API "works in browser but fails in skill", check auth first.

### 2026-04-01 — SKILL.md 從未套用 2026-03-30 修正：lesson 寫了但 SKILL.md 沒改
- **Friction**: 2026-03-30 已記錄修正方案（raw curl → SDK/CLI），但 SKILL.md 仍保留 `localhost:8830` 的 raw curl 指令。每次搜尋都靜默 fallback 到本地檔案。
- **Fix**: SKILL.md Pre-Search + Report Output 兩節全面改寫為 `core/cli/intelflow.py` CLI 調用。移除 file fallback，改為失敗時明確警告使用者。
- **Rule**: Lesson 記錄修正方案後，必須同步修改 SKILL.md。Lesson 是診斷紀錄，不是修正本身——「知道問題」≠「修好問題」。

### 2026-06-11 — Perplexity CF block defeats camoufox
- **Friction**: Perplexity leg failed — Cloudflare challenge blocked camoufox (--headed --persistent master profile) entirely; browser agent burned ~85s/50k tokens before giving up.
- **Fix**: WebSearch researcher leg ran in parallel and returned HIGH-confidence sourced answer alone; synthesis proceeded without Perplexity.
- **Rule**: For current-events queries, always pair the Perplexity browser leg with a parallel WebSearch researcher leg (not as sequential fallback) — CF blocking is now frequent enough that Perplexity must be treated as best-effort. Also: verify subagent factual details (researcher mislabeled CogVideoX as Alibaba/HKUST; it's Zhipu/Tsinghua) before saving the report.

### 2026-07-02 — 背景 researcher 的結果要從轉錄檔撈
- **Friction**: 以 name 命名的背景 researcher agent 完成後只送 idle_notification，SendMessage 不在 researcher 工具集內，主線收不到彙整內容。
- **Fix**: 直接讀 `~/.claude/projects/<project>/<agent-uuid>.jsonl`，取最後一個 assistant text block 即為 agent 的最終回覆。
- **Rule**: smart-search 並行 leg 若不需要交錯溝通，改用 `run_in_background: false` 同步取回；若必須背景跑，完成後直接解析轉錄檔，不要對 researcher 發 SendMessage 等回覆。

### 2026-07-02 — 本機除錯型查詢需加 local-evidence leg
- **Friction**: 「為什麼我的 X 會鬼打牆」是 debugging 查詢，DeepWiki/GitHub issues 只給架構背景（護欄機制），無法定案
- **Fix**: 網路兩路之外並行本機 ground-truth（~/.config/herdr/*.log、ps 血緣追蹤、shell profile grep），resize log + process tree 直接定罪
- **Rule**: 查詢主詞含「我 / my / 本機症狀」時，Route A/B 之外必加 local-evidence leg；web 查機制、本機查事實，交叉才成立

### 2026-07-03 — 「根據我的情況」類查詢需並行本機盤點
- **Friction**: 無（順跑），但此類查詢若只跑搜尋 backend 會缺個人化素材
- **Fix**: 在派 DeepWiki/researcher 的同一輪，並行 Bash 盤點本機實況（binary 版本、config 有無、實際使用痕跡如 zoxide 歷史/tmux sessions）
- **Rule**: query 含「根據我的情況/最適化推薦」→ 搜尋 leg + 本機 context leg 必須並行，綜合時以本機缺口（如缺 config）為建議主軸

### 2026-07-03 — 背景 researcher 只發 idle 通知不回結果
- **Friction**: 派 researcher（run_in_background 預設）跑 web 查證，完成時只收到 idle_notification，findings 沒有隨通知回傳；另外主線曾誤發空 AskUserQuestion 想「等待」。
- **Fix**: 用 SendMessage 向該 agent 索取 findings（請它回傳 to main），一次即取回完整結果；等待背景 agent 的正確方式是直接結束本輪，通知會喚醒主線。
- **Rule**: 背景 agent idle ≠ 結果已送達 — 收到 idle 先 SendMessage 拉結果；不要用任何工具調用來「空等」。

### 2026-07-04 — 整合可行性題要加本機實測腿
- **Friction**: DeepWiki 答「cmuxOnly 預設擋外部進程」屬文件層描述；單靠兩個遠端研究腿無法確認本機實際行為（socket 路徑還與 CLI 預設不符）
- **Fix**: 與 DeepWiki/Perplexity 並行加開本機 probe（cmux ping / lsof / capabilities），實測 Broken pipe 定案，並發現 last-socket-path 指舊路徑、真 socket 在 ~/.local/state/cmux/
- **Rule**: 「X 與 Y 可以一起用嗎」類查詢若工具已在本機，並行加一條 hands-on 驗證腿；文件說的閘門/路徑以實測為準

### 2026-07-05 — 版本歸屬必以官方 CHANGES 定案
- **Friction**: researcher 腿把 tmux popup resize 規則的 changelog 行誤歸 3.6b，DeepWiki 腿說 3.3，兩腿矛盾
- **Fix**: curl 官方 CHANGES 檔 grep 行號 + 比對 `CHANGES FROM` 區段邊界，30 秒定案（3.3）
- **Rule**: 兩腿對「版本/日期」類事實矛盾時，不要加權投票，直接抓 primary source（changelog/release notes）行級驗證

### 2026-07-05 — 「A 環境通 B 不通」先追進程鏈再搜社群
- **Friction**: 「社群有沒有類似問題」的直覺是先派 researcher 廣搜；但 cmux popup 縮放案的決定性證據全來自本機鏈：`ps -t <tty>` 追出 client 掛在 cmux 不在 Ghostty → `brew cat --cask` 拿 repo slug → `gh search issues/commits` 逐關鍵字收斂 → 抓 Swift 源碼 grep NSEvent override → `gh search commits "rightMouseDragged"` 一發命中修復 commit → compare API 確認未進 stable
- **Fix**: researcher 只留給廣域補充腿；repo 可定位時，gh CLI（search issues/commits + compare + pr view）在主線跑比 researcher 快一個數量級且零幻覺
- **Rule**: 症狀能做 A/B 環境對照時，先定罪「哪一層」（進程鏈/TERM），再對該層的 repo 用 gh CLI 精準考古；「找社群前例」的最短路徑常是 `gh search commits <API名>` 直接找修復 commit，而不是搜 issue 標題

### 2026-07-05 — changelog 措辭 ≠ 現行 master 行為（--HEAD 使用者）
- **Friction**: 3.3 CHANGES 寫「resizing works on the right and bottom borders」，但現行 master popup.c 已改為鍵位決定（左鍵拖邊框=移動、右鍵=縮放）；前一日照 changelog 措辭用左鍵拖右/下邊框 → 只會移動，誤判為「不支援 resize」，且 man page 全程未文件化此功能
- **Fix**: 對 brew --HEAD 安裝的工具（本機 tmux next-3.8），行為查證直讀 master 原始碼行級邏輯（popup.c popup_key_cb/popup_handle_drag）；changelog 只拿來定「版本歸屬」，不拿來當「操作指南」
- **Rule**: 使用者裝的是 HEAD/master 時，操作行為以現行原始碼為準 — changelog 是歷史快照，措辭可能已被後續 commit 推翻；「功能不存在」的結論必須先排除「手勢/觸發方式錯誤」

### 2026-07-06 — YouTube 影片內容 + 畫面元素辨識查詢
- **Friction**: WebFetch YouTube watch page 只回 footer；影片描述欄與網路搜尋都查不到畫面中工具（keystroke overlay）的名字；靠外觀比對產品截圖連續排除三個候選（Keystroke Pro / Keystro / Keyviz）仍無法定論
- **Fix**: 兩招組合破案——(1) yt-dlp `--download-sections` 抽關鍵段落幀 + ffmpeg tile 拼貼快速目視定位畫面元素；(2) yt-dlp `--write-comments` 撈同頻道「觀眾最可能問這題」的熱門影片留言，grep keycast/overlay/what app，命中作者本人親答
- **Rule**: 「影片畫面裡那是什麼工具」類問題，正解優先序：頻道熱門影片留言區（作者親答率高）> 影格取證外觀比對 > 描述欄/dotfiles。yt-dlp 留言抓取 + Python grep 是低成本高命中的 ground-truth 路徑；WebFetch 對 YouTube watch page 無效，影片 metadata 一律走 yt-dlp

### 2026-07-06 — YouTube 長片分析走 yt-dlp 字幕路線
- **Friction**: skill 的四條 route（DeepWiki/Context7/Perplexity）都不適用「分析 YouTube 影片內容」型查詢
- **Fix**: yt-dlp `--write-description --write-auto-subs` 抓章節+自動字幕 → python 清 VTT tag/去重 → 直讀逐字稿（44min 影片壓成 ~37K chars 可單次讀完）；影片描述的 Chapters 常直接給出工具清單骨架
- **Rule**: 查詢主體是 YouTube URL 且問「影片講/裝/做了什麼」→ 跳過 backend 選擇，直接 yt-dlp 字幕路線；zh 字幕常 429，en 即可

### 2026-07-06 — YouTube 蠶食型查詢的最優路線 = yt-dlp 中繼資料 + repo clone 深讀
- **Friction**: YouTube URL 類查詢走 WebFetch/Perplexity 拿不到實作細節；影片描述其實已含 repo 連結與架構關鍵字。
- **Fix**: yt-dlp --dump-json 先拿 title/description（免瀏覽器、3 秒內）→ 從描述抽 GitHub repo → clone 到 scratchpad 派 researcher 深讀 + --write-auto-subs 抓字幕稿派一路解析設計理念，四路並行（含自家現況盤點）一次到位。
- **Rule**: 查詢主體是 YouTube 影片且意圖是「研究實作」時，跳過 Perplexity/DeepWiki，直接 yt-dlp 中繼資料 → repo clone 路線；字幕稿補「為什麼這樣設計」，code 補「實際怎麼做」。background agent idle 無報告 → SendMessage 討報告的既有 fix 本次第 3 度驗證有效。

### 2026-07-10 — Claude Code 功能缺失類問題：binary 逆向是最強 backend
- **Friction**: 「docs 有但本機沒有」的問題，網路搜尋只能給間接推測（rollout/方案/版本），無法定論
- **Fix**: 直接 grep 本機 claude binary（`~/.local/share/claude/versions/<ver>`）抽出指令註冊碼與 isEnabled 條件，10 分鐘內拿到 gate 名（tengu_sage_compass2）與 escape hatch 環境變數，形成鐵證
- **Rule**: 查 Claude Code 自身行為時，把「本機 binary 字串/程式碼抽取」當作與 DeepWiki/Perplexity 並列的一路探針，並行派 claude-code-guide agent 查文件面；兩路交叉最快收斂

### 2026-07-10 — Cloudflare 403 站點靠 WebSearch 雙輪交叉驗證即可
- **Friction**: bridgemind.ai / docs.bridgemind.ai / vibecademy.ai 對 WebFetch 全回 403（CF bot 防護），直接抓不到首頁
- **Fix**: 不開 browser agent，改跑兩輪不同角度 WebSearch（"what is it" + "founder/pricing/review"），結果互相印證後直接合成
- **Rule**: 「這網站是什麼」級別的查詢，目標站 403 時先試第二輪換角度 WebSearch；兩輪事實一致即足夠，camoufox 留給需要互動或搜尋結果貧乏的情況

### 2026-07-12 — 小型新 repo 評估：跳過 DeepWiki，關鍵是本機 ground-truth
- **Friction**: Route A 預設 DeepWiki+Perplexity，但 296-star 新 repo DeepWiki 大概率未索引，Perplexity browser leg 成本高
- **Fix**: WebFetch README + WebSearch 雙 leg 已足；真正加值的是把 repo 揭示的機制（`claude agents --json`）在本機直接驗證存在性與輸出
- **Rule**: 「這 repo 對我們有幫助嗎」類查詢 → 抓 README 後，找出它依賴的底層機制並本機 probe，比多開搜尋 leg 更有鑑別力

### 2026-07-16 — mcpproxy 未註冊 deepwiki server，Route A 的 DeepWiki leg 形同虛設
- **Friction**: SKILL.md Route A/B 假設 mcpproxy 有 deepwiki server，實際 retrieve_tools 查無此 server，agent 自行 fallback 到 WebFetch README（幸好 prompt 有寫 fallback 步驟）
- **Fix**: agent prompt 內建 fallback 指令救回這一 leg；Perplexity leg（camoufox）本次正常，兩源交叉仍完成
- **Rule**: 派 DeepWiki leg 的 prompt 必附 README WebFetch fallback；若 deepwiki server 持續缺席，應把 SKILL.md 的 DeepWiki 路線改寫或補註冊 mcpproxy。另：兩源版本號不一致時以第一手（README/release page)為準，二手來源的「官方支援」類背書聲明未經第一手驗證要標存疑

### 2026-07-16 — mcpproxy 中 deepwiki server 預設停用
- **Friction**: DeepWiki leg 的 general-purpose agent 發現 mcpproxy 裡 deepwiki server 是停用狀態，需先啟用才能 ask_question
- **Fix**: agent 暫時啟用 → 查詢 → 恢復停用（設定淨變更為零），三次查詢均成功
- **Rule**: 派 DeepWiki leg 時在 prompt 中預告「若 server 停用，暫時啟用並於完成後恢復原狀」，避免 agent 卡在 server unavailable 就放棄

### 2026-07-16 — DeepWiki server 斷線時 WebFetch+WebSearch 雙路足以覆蓋 repo 識別查詢
- **Friction**: Route A 的 DeepWiki leg 回 `Server 'deepwiki' is not connected (state: Disconnected)`，mcpproxy 需 upstream_servers 重連
- **Fix**: 未走重連 rabbit hole，直接 WebFetch repo 頁 + WebSearch 補社群脈絡，「這是什麼」等級查詢資訊已完整
- **Rule**: 識別型 GitHub 查詢（這是什麼/who made this）DeepWiki 非必要；斷線時 WebFetch(repo 頁)+WebSearch 即可，DeepWiki 留給架構深問。另：star 數以 GitHub live 頁為準，新聞文章數字常落後數月

### 2026-07-16 — awesome-list 型 repo 直讀優於 DeepWiki/Perplexity
- **Friction**: 清單型 repo（awesome-*）走 Route A 派 DeepWiki/browser agent 是繞路；且 awesome-claude-code 2026 重構後高星經典全在 README_ALTERNATIVES/（HTML table 格式），只抓主 README 會漏掉 top-20 的 14 席
- **Fix**: curl raw README（主+legacy）→ 正則抽 owner/repo（markdown 連結與 href 兩種格式）→ GitHub GraphQL 每批 80 個 alias 批次查星數（280 repos 4 次呼叫搞定）
- **Rule**: 查詢對象是「清單/目錄型 repo」時跳過 DeepWiki/Perplexity，直讀 raw 檔案 + gh api graphql 批次充實 metadata；記得檢查 repo 有無 legacy/archive 子目錄

### 2026-07-19 — YouTube 影片 + GitHub 專案複合查詢路由
- **Friction**: 影片型 query 無專屬 route；WebFetch 對 YouTube 頁面拿不到 transcript，靠 researcher 以「影片標題 WebSearch + 二手報導」還原論點。另：兩來源 stars 數不一致（61k vs 72.4k）。
- **Fix**: 三路並行（researcher=影片解析、researcher=生態調查、inline DeepWiki=架構問答），影片論點交叉比對 DeepWiki 事實；數字衝突如實標註範圍不硬選。
- **Rule**: 「受影片啟發想研究 X 工具」類 query = 影片解析 leg + 工具生態 leg + DeepWiki 架構 leg 並行；影片內容以周邊報導/創作者 blog 三角定位，數據衝突標範圍。

### 2026-07-20 — Orca session history 以官方 docs 作為 UI contract
- **Friction**: Orca 的 session history 同時涉及 sidebar、transcript store、resume command 與 worktree scope，單看產品首頁容易把它誤讀成 tmux pane 功能。
- **Fix**: 直接查官方 session-history、agents-sessions、hibernation docs，抽出 scope、group、row actions、resume fallback 與 on-disk transcript 邊界，再對照 Workshop 的 `/api/sessions`、`/api/panes`、`/api/agents`。
- **Rule**: 研究 agent product 的 UI 模式時，優先用官方 feature page 還原 interaction contract，再用本地 runtime/API 對照，不以 screenshot 或 marketing copy 推斷資料模型。

### 2026-07-22 — ego-lite 要分開看開源 harness 與閉源 browser app
- **Friction**: GitHub repo 的 README 把「瀏覽器產品」與「agent skill/runtime」放在同一個敘事裡，容易誤以為 repo 包含完整 browser。
- **Fix**: 同時讀 README、AGENTS.md、`ego-browser` skill、install reference 與 release page，確認 repo 是 Node/CDP harness 和 skill package，真正的 Chromium app 是另行下載的閉源元件。
- **Rule**: 評估 AI browser repo 時，先切開 runtime、skill、app binary 三個信任面，再比較登入資料繼承、隔離 workspace 與平行 agent 能力。

### 2026-07-23 — Orca 跨 CLI 協調：先區隔終端管理與結構化編排
- **Friction**: 「可以協調不同 CLI agent」容易被誤解成 agents 共享上下文或由同一模型統一推理。
- **Fix**: 用官方 Supported agents、Worktrees、Orchestration 三頁交叉驗證；前兩者是 CLI process + worktree 隔離，後者才提供持久訊息、task、dispatch 與 decision gates。
- **Rule**: 解釋多 CLI agent 工具時，固定分出 process 啟動、檔案隔離、狀態觀測、任務通訊四層；明確說明是否真的有共享記憶或自主協商。

### 2026-07-23 — 工具比較文章先找出各自補的協作層
- **Friction**: Claude Squad、Herdr、Orca 都被歸成「多 agent 工具」，直接比較功能會掩蓋它們分別處理隔離、觀測與工作面的差異。
- **Fix**: 先用官方 README 與文件把每個工具映射到單一主要協作層，再用本機程式碼驗證自製工具落在哪個缺口。
- **Rule**: 寫多 agent 工具文章時，先畫出隔離、觀測、訊息、CLI 相容、治理五層，再談產品或自製工具；避免把同時啟動多個 CLI 說成共享上下文或完整編排。

### 2026-07-26 — 使用者直接給 URL 時跳過 Step 0/1 分類
- **Friction**: 參數是單一 URL（Anthropic blog）而非搜尋詞，走 Step 0 GitHub 偵測/backend 分類是空轉；同時 WebSearch 回 400（`output_config.effort 'xhigh' is not supported when thinking is disabled`）——harness 層限制，非查詢問題。
- **Fix**: 直接 WebFetch 兩趟（第一趟逐節全文、第二趟只要逐字引句與數字），交叉比對後綜合；WebSearch 失敗不重試，主文已自足。
- **Rule**: 參數是 URL → 直接 WebFetch，不跑分類；長文用「全文結構」+「逐字引句」兩趟不同 prompt 打同一 URL（15 分鐘快取內第二趟幾乎零成本），可補小模型摘要的細節流失。WebSearch 在高 effort 且 thinking 關閉時會 400，視為環境限制直接改用 WebFetch。

### 2026-07-31 — Open-Meteo 多參數 API 需避開 browser.open URL 編碼
- **Friction**: `browser.open` 將 query string 的 `&` 轉為 `%26`，使 Open-Meteo 將多個參數誤判為單一 latitude 值而回 400。
- **Fix**: 以瀏覽器頁面內的 `fetch()` 發出 API 請求，並用 `page.waitForFunction` 等待結果寫入 DOM；取得高雄七日降雨機率與降水量。
- **Rule**: Browser 工具對多參數 API URL 出現 `%26` 時，不重試導航；改用頁內 `fetch()` 取得 JSON，並回報 URL 編碼缺陷。

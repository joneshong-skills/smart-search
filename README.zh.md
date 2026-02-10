[English](README.md) | [繁體中文](README.zh.md)

# Smart Search

一個 Claude Code 技能，智慧地將搜尋查詢路由到多個後端 — **DeepWiki**、**Context7** 和 **Perplexity Pro** — 以最低成本提供最佳答案。

## 功能特色

Smart Search 根據查詢類型自動選擇最佳搜尋後端：

| 查詢類型 | 主要後端 | 備援 |
|---|---|---|
| 函式庫 / 框架文件 | DeepWiki（免費、無限制） | Context7（精確、每月 1000 次） |
| GitHub 倉庫架構 | DeepWiki | — |
| 時事新聞 | Perplexity Pro | — |
| 一般研究與比較 | Perplexity Pro | — |
| 混合 / 多來源 | 並行組合 | — |

**核心設計原則：** 函式庫問題總是優先嘗試 DeepWiki（免費且無限制）。Context7 保留作為精確補充，用於確切的 API 簽名和最新語法。Perplexity 處理時事新聞並作為最終備援。

### 配額管理

Context7 每月有 1,000 次呼叫限制。技能自動追蹤用量，配額用盡時自動退回 DeepWiki — 絕不浪費不必要的呼叫。

## 安裝

1. 將此倉庫複製或 clone 到 Claude 技能目錄：

   ```bash
   git clone https://github.com/joneshong-skills/smart-search.git ~/.claude/skills/smart-search
   ```

2. 確認 Claude Code 環境中有以下 MCP 伺服器可用：
   - `deepwiki` — 用於免費、無限制的函式庫/倉庫文件查詢
   - `context7` — 用於精確、版本特定的 API 文件
   - `playwright` — 用於 Perplexity Pro 網頁搜尋

3. 當您要求 Claude 搜尋、查詢文件、研究主題，或使用觸發詞如「搜尋」、「查一下」、「幫我找」等時，技能會自動啟動。

## 使用方式

直接自然地詢問 Claude。範例：

- *「搜尋 Next.js App Router 遷移指南」*
- *「查一下最新的 React Server Components API」*
- *「幫我找 TypeScript 6.0 的最新消息」*
- *「研究資料庫連線池的最佳實踐」*

### 查看 Context7 配額

```bash
python3 ~/.claude/skills/smart-search/scripts/usage_tracker.py status
```

## 專案結構

```
smart-search/
├── SKILL.md                        # 技能定義及路由邏輯
├── README.md                       # 英文說明
├── README.zh.md                    # 繁體中文說明（本檔案）
├── data/
│   └── usage.json                  # Context7 每月用量追蹤
├── references/
│   └── search-strategy.md          # 詳細決策樹和工作流程文件
└── scripts/
    └── usage_tracker.py            # Context7 配額追蹤腳本
```

## 授權

MIT

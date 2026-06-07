# Report I/O — Pre-Search Check, Save, and Async Slides

## Pre-Search: Check Existing Reports

Before executing any search, check if a similar report already exists:

```bash
~/.local/bin/intelflow reports check "<user query>" --threshold 0.7
# For JSON output: ~/.local/bin/intelflow --json reports check "<user query>"
```

- If match found → ask user "找到相似的研究報告，要直接查看還是重新搜尋？"
- View full report: `~/.local/bin/intelflow reports get <id>`
- If no match or error → proceed to normal search flow

## Report Output

Every search result MUST be saved via the `intelflow` CLI.

**Steps**:
1. After synthesizing the final answer, write to temp file then pipe via stdin:
   ```bash
   cat > /tmp/report.md << 'EOF'
   ... report content ...
   EOF
   cat /tmp/report.md | ~/.local/bin/intelflow reports create \
     --title "..." --query "..." \
     --content - \
     --tags "..." --sources '[...]' --skill "smart-search"
   ```
   - **`--content -`** reads from stdin — avoids shell escaping issues
   - **`--content @/tmp/report.md`** also works (reads file directly)
   - Short content can still be passed inline: `--content "short text"`

2. Output: `Report created: <id>` — include this in the response footer.

3. **Fallback**: If CLI errors, write to `${CLAUDE_OUTPUTS_DIR:-~/workshop/outputs}/smart-search/{YYYY-MM-DD}-{slug}.md`

**Tags guideline**: 3-8 relevant, comma-separated. Used for automatic topic extraction.

## Async Slide Generation (Background Mode)

When the user asks to create slides/deck/presentation (`簡報`, `投影片`, `slides`, `pptx`):

1. Search + synthesis stay synchronous (normal flow)
2. Save the research report first (Report Output section above)
3. Start slide generation as a background job using `Bash` (`nohup ... &`)
4. Return immediately without waiting for render completion

Use this pattern:

```bash
mkdir -p "${CLAUDE_OUTPUTS_DIR:-~/workshop/outputs}/smart-search/jobs"
nohup <deck-generation-command> \
  > "${CLAUDE_OUTPUTS_DIR:-~/workshop/outputs}/smart-search/jobs/<job-slug>.log" 2>&1 &
echo $!
```

Response requirements for async deck requests:
- Include `Job PID`
- Include expected deck output path
- Include log path
- Include a status check command:
  `ps -p <PID> -o pid=,etime=,state=,command=`

Do not block on deck generation unless the user explicitly asks to wait.

# Non-Obvious Features Guide

Things that aren't immediately obvious but make the system powerful.

## 1. Logical Day Boundary (03:00)

**Problem:** You work until 2 AM. Midnight rolls over. Your reflection for "today" now includes zero hours of work.

**Solution:** `get_today()` returns `logical_today` — the date shifts at 03:00, not midnight.

```
Real time: 2024-03-07 02:30 AM
Real date: 2024-03-07
Logical today: 2024-03-06  ← use this for reflections
```

**When to use which:**
- `logical_today` → session notes filenames, daily reflections, retros
- Real date → calendar events, deadlines, task creation

## 2. Session Notes as Institutional Memory

After significant work in VS Code, save what happened:

```markdown
# conversations/2024-03-06_setup-monitoring.md

## What was done
- Configured brain-monitor PM2 process
- Set up Telegram alerts for CPU/RAM/disk
- Added 30-minute cooldown between alerts

## Decisions made
- Alert thresholds: CPU 80%, RAM <1GB, Disk 85%
- Cooldown 30 min (not per-metric, global)

## Open questions / next steps
- Should we add custom alert channels?
```

**Why this matters:** Next time you (or Claude) work on monitoring, reading this file gives full context. Claude doesn't need to re-discover decisions or re-investigate the setup.

**Pro tip:** After creating/modifying any service, script, or making an architectural decision, Claude should proactively suggest: "Save session notes?"

## 3. Dashboard is Append-Only Safe

The dashboard uses section parsing to modify in place:

```python
update_dashboard("add", "Set up nginx reverse proxy", "server")
# → Appends to "## Active Tasks" section

update_dashboard("complete", "nginx")
# → Finds task matching "nginx" in Active, moves to Completed with date

update_dashboard("remove", "nginx")
# → Removes matching task entirely
```

**Why not just `write_vault("dashboard.md")`?** Because it overwrites the entire file. If Claude's context is stale (compressed away earlier dashboard content), you lose tasks.

## 4. Semantic Search is Multilingual

The ONNX model (`paraphrase-multilingual-MiniLM-L12-v2`) supports 50+ languages. You can:

- Write notes in any language
- Search in any language
- Cross-language search works (search in English, find Russian docs)

**Example:**
```
semantic_search("how to set up monitoring")
→ finds "Server monitoring setup.md"
```

## 5. Voice Message Pipeline

When a voice message arrives via Takopi:

1. Takopi receives the audio from Telegram
2. Routes to Brain's Whisper server (`:8787`)
3. Whisper routes: ≤4min → local faster-whisper, >4min → Groq API
4. Transcript returned to Takopi → shown in Claude Code
5. Claude decides: idea → `write_vault("inbox/...")`, question → answer directly

**What to save:** Ideas, plans, notes, todos
**What NOT to save:** Simple questions, routine commands

## 6. Context Files as Distributed Index

Instead of one giant index file, each folder has its own `FOLDER_NAME.md`:

```
vault/
├── inbox/INBOX.md          # "What's in inbox and how to process it"
├── decisions/DECISIONS.md  # "How to write decision notes + list of all decisions"
├── retro/RETRO.md          # "Retro format + list of all retros"
```

**Why?** Claude reads one context file to understand a folder. No need to scan the whole vault. It's like having a librarian in every room.

**Maintenance:** When you add a file to a folder, update its context file. The Librarian audits for mismatches weekly.

## 7. Bidirectional Links

If document A references document B, document B should reference A back:

```markdown
# projects/brain.md
Related: [[decisions/2024-03-01_embedding-model]]

# decisions/2024-03-01_embedding-model.md
Related: [[projects/brain]]  ← THIS must exist
```

**Why?** Navigation. When Claude reads a decision note, it can find all related projects. When reading a project, it can find all decisions.

## 8. Escalating Reminders

The 4-level escalation pattern prevents procrastination:

```
Level 1 (3h before deadline): Detailed stats, context, motivation
Level 2 (1h later):           Simple "Hey, don't forget"
Level 3 (1h later):           "Last chance" with action buttons
Level 4 (auto):               Just do it automatically
```

**Key insight:** Level 4 auto-executes. For retros, it generates a basic retro automatically. For content plans, it marks the review as done. This ensures nothing gets completely dropped.

**Marker files** prevent re-running: once the task is done (at any level), remaining levels skip.

## 9. Dual-Channel Ask

When Claude needs your input:
- You might be at your desk (VS Code)
- You might be on your phone (Telegram)

Dual-channel sends to BOTH. First answer wins.

```
Claude → sends question to Telegram (buttons)
Claude → prints question in VS Code (text)
Claude → polls Telegram in background

You answer in Telegram → Claude gets it
   OR
You type in VS Code → Claude cancels Telegram question
```

**Implementation detail:** Never use `AskUserQuestion` (VS Code only). Always use the dual-channel workflow.

## 10. Calendar Source Tracking

Events aren't just dates — they link back to their source:

```python
add_calendar_event(
    title="Ship feature X",
    date="2024-03-15",
    source_type="trello",      # Where the task lives
    source_id="card_abc123"    # How to find it
)
```

**Why?** The hourly `calendar-sync.py` cron checks: "Is this Trello card still open? No? Remove the calendar event." This prevents stale deadlines from cluttering the calendar.

## 11. Fail-Safe Calendar Sync

Three-part strategy (runs hourly):

1. **Process queue:** Execute pending `queue_calendar_sync()` actions from Claude
2. **Fail-safe check:** For each event with a `source_type`, verify the source task still exists and is open
3. **Cleanup:** Remove events older than 14 days

**Never deletes without verification.** If the source system is unreachable, the event stays.

## 12. Debounced Git Sync

When `write_vault()` is called:
1. Cancel any pending sync timer
2. Start a 30-second countdown
3. If another write happens within 30s → reset the timer
4. When timer fires → single git commit with all changes

**Result:** Creating 10 files in a row → 1 git commit (not 10).

## 13. Incremental Embedding Updates

Full index rebuild takes 30-60 seconds. But when you write one file:
1. Only that file's chunks are re-embedded
2. Old chunks for that file are replaced
3. Rest of the index stays the same

**Staleness detection:** Each chunk records the file's `mtime`. On search, if any chunks are stale, they're re-indexed before searching.

## 14. Librarian Audit Agent

Runs weekly (Monday 4 AM). Not a script — an actual Claude Code agent with read-only access to the vault.

**Two-pass architecture:**
- **Pass 1 (fast):** Structure checks, missing files, index consistency
- **Pass 2 (deep):** Semantic deduplication, cross-document contradictions, freshness scoring

**History tracking:** All findings get unique IDs in `history.json`. Fixed findings are marked as resolved. This prevents re-reporting the same issue every week.

**Report delivery:** Full report saved locally + compressed version sent via Telegram.

## 15. Decision Notes

When you make a significant decision (tech choice, architecture, workflow), save it:

```markdown
# decisions/2024-03-01_embedding-model.md

## Context
Need semantic search for vault. Options: OpenAI API, local ONNX, ChromaDB.

## Options Considered
1. **OpenAI embeddings** — best quality, requires API key, costs money
2. **Local ONNX** — good quality, runs on CPU, free, no network
3. **ChromaDB** — overkill for vault size

## Decision
Local ONNX with `paraphrase-multilingual-MiniLM-L12-v2`.

## Reasoning
- No API dependency (works offline)
- Multilingual (vault has Russian + English)
- 384-dim is compact enough for CPU
- Good enough quality for knowledge search
```

**Why?** Three months later, when you wonder "why didn't we use OpenAI embeddings?", the answer is right there.

## 16. Path Security

All vault operations validate paths:
- **Directory traversal:** `../../etc/passwd` → blocked
- **Symlink attacks:** symlinks outside vault → blocked
- **Sensitive patterns:** `.env`, `.ssh`, `*-token.json`, `*-api-key.json` → blocked from ingestion

## 17. Task Routing

Different task types go to different systems:

| Category | Destination | Tool |
|----------|------------|------|
| Personal tasks, shopping, errands | Trello | `trello_create_card` |
| Server infra, brain, pet projects | `dashboard.md` | `update_dashboard("add")` |
| Work project tasks | Work task manager | Bitrix/Jira/etc |

The `/track` skill automates this: describe a task, it figures out where it goes.

## 18. MEMORY.md as Core Rules

`MEMORY.md` is always loaded into Claude's context. Use it for:
- **Absolute rules:** "NEVER use AskUserQuestion", "ALWAYS call get_today() before dates"
- **Verified patterns:** Stable conventions confirmed across multiple sessions
- **Domain knowledge links:** Point to topic files for detailed info

**Keep it under 200 lines** — everything after line 200 gets truncated.

## 19. Auto-Memory (Claude Learns)

Claude Code automatically learns your preferences and saves them to memory files:
- First time: "I prefer tabs over spaces" → Claude remembers
- Recurring: "This user always wants tests run after changes" → saved
- Corrections: "Actually, use 2-space indent" → memory updated

Over time, Claude becomes more aligned with your workflow without you repeating yourself.

## 20. Skills as Composable Workflows

Skills can call MCP tools, read vault files, and even invoke other skills. Examples:

- **`/retro`** — reads Trello done stats → generates reflection → saves to vault → archives week → sends to Telegram
- **`/reflect`** — gathers from 11 task sources → cross-references session notes → produces daily synthesis
- **`/track`** — analyzes task description → routes to correct system → confirms

**Creating your own:** Copy `skills/example/SKILL.md`, customize triggers and instructions.

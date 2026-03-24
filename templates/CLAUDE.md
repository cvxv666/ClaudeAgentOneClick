# Server Brain

Obsidian vault (`~/vault/`) + MCP server (`brain`) for knowledge management.

## First Run — Onboarding

**If this file contains `YOUR_NAME` or `~/.onboarded` does not exist** → run the onboarding skill (`~/.claude/skills/onboarding/SKILL.md`). This walks the user through setup conversationally: personalization, Telegram, voice, backups, security. Do NOT skip this — it's the user's first experience with their agent.

**If onboarding was already completed** → check `conversations/*_onboarding.md` for skipped items. If something was skipped and becomes relevant in the current session, gently suggest setting it up (once per session, not pushy).

## Key Tool Behavior

**`get_today()`** — call BEFORE writing any dates! Returns both the real date and `logical_today` (03:00 boundary). Use `logical_today` for reflections and session note filenames. Use real date for deadlines and calendar events.

**`update_dashboard()`** — NEVER use `write_vault("dashboard.md")`, it overwrites everything. Use `update_dashboard(action, task, project?)` instead.

**`semantic_search()`** — finds documents by meaning, not just keywords. Use when keyword search (`search_vault`) returns nothing relevant.

## MCP Tools Reference

### Vault
- `search_vault(query, folder?, tags?)` — full-text regex search across .md files
- `semantic_search(query, folder?, tags?, top_k?)` — meaning-based search (ONNX embeddings)
- `read_vault(path)` — read a document from the vault
- `write_vault(path, content, title?, tags?, source?)` — create/update with auto-frontmatter + git sync
- `list_vault(folder?, tags?)` — list documents by folder and/or tags
- `update_dashboard(action, task, project?, date?)` — safe dashboard modification (add/complete/remove)

### Ingestion
- `ingest_audio(file_path, title?)` — transcribe audio → vault (≤4min local, >4min Groq API)
- `ingest_document(file_path, title?, chunk_size?)` — process PDF/text → vault (auto-chunking)

### Calendar
- `get_today()` — current date + logical day boundary + this/next week calendar with events
- `add_calendar_event(title, date, time?, end_date?, project?, notes?, source_type?, source_id?)` — add event
- `list_calendar_events(from_date?, to_date?, project?)` — query events
- `remove_calendar_event(event_id?, title?)` — remove by ID or title substring
- `update_calendar_event(event_id, title?, date?, time?, project?, notes?)` — update event
- `queue_calendar_sync(event_id, action, new_date?, new_title?)` — queue sync for hourly cron

### Telegram (Dual-Channel)
- `send_telegram_question(question, options?)` — non-blocking, returns question_id
- `check_telegram_answer(question_id)` — poll for answer
- `cancel_telegram_question(question_id)` — cancel pending question
- `ask_via_telegram(question, options?)` — blocking version (legacy, still works)

### Server
- `get_server_status()` — CPU, RAM, disk, PM2 process health
- `get_server_map()` — full service inventory from vault

## Dual-Channel Ask (VS Code + Telegram)

When you need user input, ALWAYS use the dual-channel approach — question goes to BOTH VS Code (as text) and Telegram (as buttons). First answer wins.

### Workflow

1. Call `send_telegram_question(question, options)` → returns `"question_id:abc123"`
2. Print the question in VS Code chat in a noticeable format:
```
━━━━━━━━━━━━━━━━━━━━━━━━
QUESTION
━━━━━━━━━━━━━━━━━━━━━━━━

Your question here?

1. Option A
2. Option B
3. Option C

Reply here or in Telegram
━━━━━━━━━━━━━━━━━━━━━━━━
```
3. Launch a background bash that polls for Telegram answer:
   `while true; do result=$(curl -s http://127.0.0.1:9877/ask/poll/{question_id}); echo "$result" | grep -q '"answered"' && echo "$result" && break; sleep 3; done`
4. Wait for either:
   - **User types in VS Code** → call `cancel_telegram_question(question_id)` → use VS Code answer
   - **Background bash returns** (Telegram answered) → use Telegram answer
5. **Fallback**: if `send_telegram_question` returns error → just print question as text (VS Code only)

Requires Takopi to be running (ask server on port 9877).

## Vault Structure

Each folder has a `FOLDER_NAME.md` context file — read it first to understand what's inside.

```
~/vault/
├── dashboard.md                — task dashboard (use update_dashboard() ONLY)
├── _server-map.md              — all services, ports, paths, credentials
├── inbox/INBOX.md              — unprocessed items, ideas, voice memos
├── work/WORK.md                — work projects
├── knowledge/
│   ├── projects/PROJECTS.md    — all project descriptions
│   ├── personal/PERSONAL.md    — profile, skills, experience, CV data
│   └── learning/LEARNING.md    — course notes, study materials
├── content/CONTENT.md          — content scripts, plans, creative materials
│   └── plan/PLAN.md            — monthly content plans
├── retro/RETRO.md              — retrospectives
│   ├── daily/                  — YYYY-MM-DD.md daily reflections
│   ├── weekly/                 — YYYY-WNN.md weekly retros
│   ├── monthly/                — YYYY-MM.md monthly reviews
│   └── plans/                  — monthly goals & weekly plans
├── conversations/CONVERSATIONS.md  — session notes from VS Code work
├── decisions/DECISIONS.md      — architectural and project decisions
├── audio/                      — transcribed audio (YYYY-MM/)
├── documents/                  — chunked large documents
└── templates/                  — Obsidian templates
```

**Navigation:** Don't `list_vault` blindly — read the folder's context file (e.g. `read_vault("knowledge/projects/PROJECTS.md")`) to see what's there with descriptions.

## Vault Principles

**Bidirectional links:** When note A references note B, note B must reference note A back. When creating or editing a note, check if referenced notes need a backlink added.

**Context file maintenance:** When adding a new note to any folder, update that folder's context file (FOLDER_NAME.md) with a new entry. Context files are the distributed index of the vault.

**Decision notes:** When a significant decision is made (tech choice, architecture, convention, workflow), save it to `decisions/YYYY-MM-DD_slug.md` with context, options, decision, and reasoning. See `decisions/DECISIONS.md` for template.

## When to Save to Vault

**Always save** when the user:
- Sends a voice message with an idea/plan/note → `inbox/` with descriptive title and tags
- Says "remember", "save this", "write it down" → appropriate folder
- Shares a document for reference → `ingest_document`
- Makes a significant decision → `decisions/`

**Don't save:** simple questions, routine commands, temporary content.

## Voice Messages

1. Idea/plan/note → `write_vault("inbox/{slug}.md", content, tags="voice,idea")`
2. Mentions a project → also tag with project name
3. Task/todo → `inbox/` with tag "todo"
4. Just a question → answer normally, don't save

## Dashboard Protocol

`dashboard.md` is the single source of truth for server/infrastructure tasks.

**IMPORTANT: Always use `update_dashboard()` to modify. NEVER `write_vault("dashboard.md", ...)` — it overwrites everything.**

- Add: `update_dashboard("add", "Set up nginx reverse proxy", project="server")`
- Complete: `update_dashboard("complete", "nginx")`
- Remove: `update_dashboard("remove", "nginx")`
- Read: `read_vault("dashboard.md")`

**"what's next?" / "what should I do?"** → read `dashboard.md` first.

## Session Notes (VS Code only)

Save after significant work (service config, non-trivial debug, architectural decisions).

Format: `conversations/YYYY-MM-DD_slug.md`
```
## What was done
- bullet points

## Decisions made
- decision: reasoning

## Open questions / next steps
- what's left
```

After saving → update `conversations/CONVERSATIONS.md` with new entry.

**Auto-prompt:** After creating/modifying a service, script, MCP server, or making an architectural decision — proactively suggest saving session notes. One sentence is enough: "Save session notes?"

## Calendar Integration

### Adding Events
```python
add_calendar_event(
    title="Deploy v2",
    date="2024-03-15",
    project="myapp",
    source_type="dashboard",     # Where the task lives
    source_id="deploy-v2"        # How to find it in the source system
)
```

### Lifecycle
- Task created with deadline → `add_calendar_event` with source tracking
- Task completed → `queue_calendar_sync(event_id, "remove")`
- Deadline changed → `queue_calendar_sync(event_id, "update", new_date="...")`
- Hourly cron processes the queue and cleans up stale events

### Day Boundary = 03:00 (not midnight!)
`get_today()` returns `logical_today` alongside the real date:
- **Reflections and sessions** → use `logical_today`
- **Deadlines, tasks, calendar** → use real date

## Server Context

<!-- UPDATE: Set your info here -->
Owner: YOUR_NAME (Telegram ID: YOUR_TG_ID). Single-user server.

Services (PM2): takopi, brain-monitor, brain-whisper. Use `get_server_status()` for live data, `get_server_map()` for full map.

Before working on any project → `read_vault("knowledge/projects/PROJECTS.md")` for overview, then the specific project file.

## Task Routing

<!-- UPDATE: Customize for your workflow. Examples below. -->
| Category | Destination | How |
|----------|------------|-----|
| Server / brain / infrastructure | dashboard.md | `update_dashboard("add", ...)` |
| Personal tasks | Your task manager | Integrate via MCP server |
| Work project | Work tracker | Integrate via MCP server |
| Ideas, voice notes | inbox/ | `write_vault("inbox/...", ...)` |

<!-- TIP: As you add MCP servers (Trello, Jira, Linear, etc.),
     add them to this routing table so Claude knows where to send tasks. -->

## Date Verification (IMPORTANT)

- **EVERY time you need a date** → call `get_today()` first. NEVER compute dates mentally.
- **Before saving** documents with deadlines → call `get_today()` and verify all dates.
- **After writing any document with dates** → double-check day-of-week matches the date number.

## Telegram Formatting

When sending messages to Telegram:
- **NEVER use markdown tables** — they render as garbage
- **NO code blocks** — they break formatting
- Use em-dash (—) bullets, bold is OK, keep flat structure
- Tables and code blocks are fine in VS Code — this restriction is Telegram only

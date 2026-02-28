# Server Brain

Obsidian vault (`~/vault/`) + MCP server (`brain`) for knowledge management.

## MCP Tools

- `search_vault(query, folder?, tags?)` — search by text/regex
- `read_vault(path)` — read a document
- `write_vault(path, content, title?, tags?, source?)` — create/update
- `list_vault(folder?, tags?)` — list documents
- `ingest_audio(file_path, title?)` — Whisper transcription -> vault
- `ingest_document(file_path, title?, chunk_size?)` — process PDF/text -> vault
- `get_server_status()` — CPU, RAM, disk, PM2
- `get_server_map()` — full service map
- `update_dashboard(action, task, project?, date?)` — modify dashboard tasks
- `ask_via_telegram(question, options?)` — ask user a question via Telegram

## Dual-Channel Ask (VS Code + Telegram)

When you need user input, use the dual-channel approach — question goes to BOTH VS Code (as text) and Telegram (as buttons). First answer wins.

### Workflow

1. Call `send_telegram_question(question, options)` -> returns `"question_id:abc123"`
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
   - **User types in VS Code** -> call `cancel_telegram_question(question_id)` -> use VS Code answer
   - **Background bash returns** (Telegram answered) -> use Telegram answer
5. **Fallback**: if `send_telegram_question` returns error -> just print question as text (VS Code only)

Requires Takopi to be running (ask server on port 9877).

## Vault Structure

Each folder has a `FOLDER_NAME.md` context file — read it first to understand what's inside.

```
~/vault/
├── dashboard.md                — task dashboard
├── _server-map.md              — all services, ports, paths
├── inbox/INBOX.md              — unprocessed items, ideas, voice memos
├── work/WORK.md                — work projects
├── knowledge/
│   ├── projects/PROJECTS.md    — all project descriptions
│   ├── personal/PERSONAL.md    — profile, skills, experience
│   └── learning/LEARNING.md    — course notes
├── content/CONTENT.md          — content scripts, plans
│   └── plan/PLAN.md            — monthly content plans
├── retro/RETRO.md              — weekly & monthly retrospectives
│   ├── weekly/                 — YYYY-WNN.md files
│   └── monthly/                — YYYY-MM.md files
├── conversations/CONVERSATIONS.md  — session notes from VS Code work
├── decisions/DECISIONS.md      — architectural and project decisions
├── audio/                      — transcribed audio (YYYY-MM/)
├── documents/                  — chunked large documents
└── templates/                  — Obsidian templates
```

**Navigation:** Don't `list_vault` blindly — read the folder's context file (e.g. `read_vault("knowledge/projects/PROJECTS.md")`) to see what's there.

## Vault Principles

**Bidirectional links:** When note A references note B, note B must reference note A back. This keeps the knowledge graph connected.

**Context file maintenance:** When adding a new note to any folder, update that folder's context file (FOLDER_NAME.md) with a new entry.

**Decision notes:** When a significant decision is made (tech choice, architecture, convention, workflow), save it to `decisions/YYYY-MM-DD_slug.md` with context, options, decision, and reasoning.

## When to Save to Vault

**Always save** when the user:
- Sends a voice message with an idea/plan/note -> `inbox/` with descriptive title and tags
- Says "remember", "save this", "write it down" -> appropriate folder
- Shares a document for reference -> `ingest_document`
- Makes a significant decision -> `decisions/`

**Don't save:** simple questions, routine commands, temporary content.

## Dashboard Protocol

`dashboard.md` is the single source of truth for tasks.

**IMPORTANT: Always use `update_dashboard()` to modify. NEVER `write_vault("dashboard.md", ...)` — it overwrites everything.**

- Add: `update_dashboard("add", "description", project="myapp")`
- Complete: `update_dashboard("complete", "substring")`
- Remove: `update_dashboard("remove", "substring")`
- Read: `read_vault("dashboard.md")`

**"what's next?" / "what should I do?"** -> read `dashboard.md` first.

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

After saving -> update `conversations/CONVERSATIONS.md` with new entry.

## Server Context

<!-- UPDATE: Set your info here -->
Owner: YOUR_NAME (Telegram ID: YOUR_TG_ID). Single-user server.

Services (PM2): takopi, brain-monitor, brain-whisper. Use `get_server_status()` for live data, `get_server_map()` for full map.

Before working on any project -> `read_vault("knowledge/projects/PROJECTS.md")` for overview.

## Task Routing

<!-- UPDATE: Customize for your workflow -->
| Category | Destination | How |
|----------|------------|-----|
| Server / brain / infrastructure | dashboard.md | `update_dashboard("add", ...)` |
| Everything else | dashboard.md | `update_dashboard("add", ...)` |

<!-- TIP: Add more destinations as you integrate more services.
     Example: Trello for personal tasks, Jira for work, etc. -->

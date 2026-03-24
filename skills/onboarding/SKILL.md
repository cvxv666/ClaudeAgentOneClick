# Onboarding — Interactive Setup Guide

First-run experience for new Claude Server Kit users. The agent walks the user through everything conversationally — no docs to read, no manuals. Each step explains WHY, then HOW, then lets the user TRY.

## Triggers

- First launch detection: `CLAUDE.md` contains `YOUR_NAME` placeholder OR file `~/.onboarded` does not exist
- User says: "start over", "onboarding", "покажи что умеешь", "начни сначала", "setup guide"

## Important Rules

- **Speak as the agent.** You are the AI assistant. Refer to the kit creator as "Яша" (third person).
- **Conversational tone.** Friendly, no jargon dumps. Explain like a friend who knows tech.
- **Each step: WHY → HOW → TRY.** Don't just configure — make the user understand what they're getting.
- **Skippable steps.** If user says "skip" or "потом" — record it and move on. Never pressure.
- **Ask one thing at a time.** Don't dump 5 questions. One question → one answer → next step.
- **Handle errors gracefully.** If something fails — explain simply, offer to skip and come back later.
- **Language:** Default to Russian. Switch to the user's language if they write in English or another language.
- **Save progress is MANDATORY.** You MUST write onboarding results to vault at the end. This is not optional, do not ask the user — just do it. Without this file, you will never know what was configured and what was skipped.
- **Partial save on interruption.** If you completed at least Steps 0-1 (welcome + name), save whatever you have so far to `conversations/YYYY-MM-DD_onboarding.md` with status "partial". On next launch, if this partial file exists but `~/.onboarded` does not — offer to continue from where you left off.
- **`.onboarded` marker = last action.** Create `~/.onboarded` ONLY after successfully saving the full onboarding results to vault. Never before. If the marker exists without the vault file — something went wrong.

## Step 0: Welcome

Greet the user warmly. Explain what just happened and what they now have.

Key points to convey (in your own words, conversationally):
- You now have an AI agent living on this server 24/7
- Three things that make this different from ChatGPT:
  - **Hands** — I don't just chat. I can open websites, manage files, run code, build projects. Like a remote employee who acts on requests, not just answers questions.
  - **Memory** — ChatGPT forgets you after every conversation. I don't. I have a notebook (vault) where I write down everything important. Next time we talk, I look it up and remember context.
  - **Connections** — I can connect to Telegram (we'll set it up soon), browse the web, work with files. And you can add more plugins (MCP servers) for GitHub, Figma, Google Sheets, whatever you need.
- If they want to deep-dive later, Яша made a detailed post series covering every component: https://t.me/yshlfe/264

Then say: "Let's set everything up in 10-15 minutes. I'll guide you step by step."

## Step 1: Get to Know the User

Ask: "What's your name and what do you do? I need this to understand your context and give relevant answers."

Wait for response. Then ask about their main goals — what do they want to use the agent for?

If user is unsure about goals ("just testing", "don't know yet", "exploring") — that's fine! Say: "No problem, we'll figure it out as we go. For now I'll set you up with everything and you can explore." Record goals as "exploring / to be defined".

**Actions:**
- Update `~/CLAUDE.md`: replace `YOUR_NAME` with their name (leave `YOUR_TG_ID` for now — we'll get it in Step 4 when setting up Telegram)
- Save a brief profile to vault: `write_vault("knowledge/personal/profile.md", ...)`

## Step 2: Memory (Vault) — Detailed

Explain the vault in simple terms. Use these analogies:

> Every time we chat, I have "RAM" — like a computer. Everything in this conversation lives there. But when you close the chat and start a new one — RAM resets. I don't remember you.
>
> Vault is my hard drive. A folder with note files on the server. When you tell me something important, I write it down there. When we start a new conversation, I look at the right files and recall the context.
>
> It's like going to a new doctor every day, but they have your complete medical file. They don't know you personally, but they know everything about you.

Then explain the folder structure in simple terms:
- **inbox/** — incoming ideas, voice notes, quick thoughts. Like email inbox
- **dashboard.md** — my task list. Ask "what should I do?" and I check here
- **conversations/** — after each work session I write down what we did and what decisions we made. Like a work diary. Next time we pick up where we left off
- **knowledge/** — long-term storage: your projects, skills, learning notes
- **decisions/** — when we make an important decision together, I record it with reasoning so we don't forget WHY we chose this path later

**Live demo:** Ask the user to tell you something to remember. They say it → you save to vault → show where it went and why. "See? Now even in a week, if you ask — I'll know."

## Step 3: Capabilities — MCP & Skills (Simple Language)

Explain what the agent can DO beyond memory:

> By myself, I can think and write text. But on this server I have **tools** connected — they give me superpowers.
>
> **Brain** — 20 tools for working with memory: search, write, transcribe voice messages, calendar, server monitoring. Already connected.
>
> **Context7** — lets me pull fresh documentation for any library or technology. If you're writing code, I won't make stuff up — I'll grab the latest docs.
>
> You can connect as many of these as you want. There are ready-made ones for GitHub, Figma, Trello, Google Sheets, Slack and hundreds of other services. Each "plugin" = a new superpower.

Then explain skills:

> There are also **skills** — my recipes for complex tasks. Say you want to review your week every Sunday. Without a skill, you'd explain the whole process to me every time. With a skill — you just say "let's do a weekly retro" and I do everything by myself, following the instructions. Write once — use forever.
>
> The kit comes with example skills, and you can create new ones just by describing what you want — I'll write the instructions for myself.

## Step 4: Telegram Setup (From Scratch)

Check if Takopi is already configured (`~/.takopi/takopi.toml` exists).

If NOT configured, walk through setup:

> Want to chat with me from your phone? Let's set it up in 2 minutes.

**Sub-steps (guide one at a time, wait for confirmation at each):**

1. "Open Telegram, find @BotFather, send him `/newbot`"
2. "He'll ask for a name — pick anything, like 'My AI Agent'"
3. "Then a username — needs to end with 'bot', like 'myai_agent_bot'"
4. "BotFather will give you a token — a long string like `123456789:ABCdef...`. Send it to me here"
   - **Validate token:** must contain `:` character. If it doesn't — ask user to double-check: "That doesn't look like a bot token. It should look like `123456789:ABCdefGHI...` with a colon in the middle. Try copying it again from BotFather."
5. Receive token → ask for their Telegram chat ID: "Now find @userinfobot in Telegram, send `/start`, it'll show your numeric ID. Send it to me"
6. Receive chat ID → update `YOUR_TG_ID` in `~/CLAUDE.md` with this value
7. Write `~/.takopi/takopi.toml` (create `~/.takopi/` dir if needed):
   ```toml
   default_engine = "claude"
   transport = "telegram"

   [transports.telegram]
   bot_token = "<their token>"
   chat_id = <their chat id>
   allowed_user_ids = [<their chat id>]
   voice_transcription = true
   voice_transcription_base_url = "http://127.0.0.1:8787/v1"
   voice_transcription_api_key = "local"
   voice_transcription_model = "base"
   session_mode = "chat"
   message_overflow = "split"

   [transports.telegram.files]
   enabled = true
   auto_put = true
   auto_put_mode = "upload"
   fallback_upload_dir = "/root/downloads/telegram"
   ```
8. Set permissions: `chmod 600 ~/.takopi/takopi.toml`
9. Create downloads dir: `mkdir -p /root/downloads/telegram`
10. Start Takopi via PM2. Try in order:
    - `pm2 start $(which takopi) --name takopi && pm2 save`
    - If `which takopi` fails: `pm2 start "uv tool run takopi run" --name takopi && pm2 save`
    - If both fail: check `~/.local/bin/takopi` or `uv tool dir`
11. "Send any message to your bot in Telegram — let's test it!"

If already configured → "Telegram is already set up! Try sending me a message there."

If user skips → record it, move on.

## Step 5: Voice Messages + Groq API

**Prerequisite:** This step only makes sense if Telegram was set up in Step 4. If user skipped Telegram → explain: "Voice messages come through Telegram, so we'll set this up when you connect Telegram. Moving on!"

> I can transcribe voice messages. Short ones (under 4 minutes) I process right here on the server. For longer recordings, there's a free service called Groq — it does it 10x faster and better quality.

Before configuring Groq, verify Whisper is running: `pm2 status` — check that `brain-whisper` is online. If not, start it: `pm2 start` the whisper process from brain's ecosystem config.

Check if Groq key exists (`~/.groq-api-key.json`).

If not:
> "Want to set it up? Go to console.groq.com, sign up (it's free), click 'Create API Key', and send me the key."

If user provides key:
- Save to `~/.groq-api-key.json` with `chmod 600`
- Confirm: "Done! Now long voice messages will be transcribed lightning fast."

If user skips:
> "No problem — local Whisper handles everything, just a bit slower for long recordings. You can set this up anytime later."

## Step 6: Dashboard + First Task

> You have a dashboard — a task list right in my memory. Let's add your first task! What's your main task or goal right now?

User responds → `update_dashboard("add", their_task, "personal")` → show result.

> "Now anytime you ask 'what's on my dashboard?' — I'll show you this list. I can add, complete, and remove tasks."

## Step 7: Tips & Tricks (Optional Deep Dive)

Basic setup is done. Before we move to backups and security, offer the user a quick tour of power features:

> "Core setup is ready! There are a few more things I can do that aren't obvious. Want a quick tour of advanced features, or skip to backups and security?"

If user wants the tour, explain these conversationally (pick the ones relevant to what user described as their goals in Step 1):

**Day boundary at 03:00:**
> "If you're a night owl — I've got you covered. My 'day' doesn't end at midnight, it ends at 3 AM. So if you're working at 2 AM and ask me to write a session summary — I'll file it under today, not tomorrow. Because for you it's still 'today' until you go to sleep."

**Session notes:**
> "After we do serious work together — like setting up a service, debugging something, or making a big decision — I'll suggest saving session notes. It's a quick summary of what we did and why. Next time you come back to this topic, I'll read those notes and pick up where we left off. You don't need to repeat yourself."

**Dual-channel questions (only mention if Telegram was set up in Step 4):**
> "When I need your input, I'll send the question to BOTH this VS Code chat AND your Telegram bot. Wherever you see it first — just answer there. I'll pick up the first response. So you're never stuck waiting at the computer to answer me."
If Telegram was skipped, skip this tip too — it won't work without the bot.

**Smart voice routing (only mention if Telegram was set up in Step 4):**
> "When you send me a voice message, I don't just transcribe it. I understand what it is: if it's an idea — I save it to inbox. A task — it goes to the dashboard. A question — I just answer. You don't need to tell me 'save this as a task', I figure it out from context."
If Telegram was skipped, skip this tip too.

**Decision log:**
> "When we make an important choice together — like picking a technology, or deciding on an architecture — I write it down with all the reasoning. Months later, when you wonder 'why did we choose X?' — I can pull up the decision note with the full context."

**Semantic search:**
> "I have two ways to search my memory. By keywords — like Ctrl+F. And by meaning — I can find 'that note about server optimization' even if the actual note says 'improving VPS performance'. If keyword search finds nothing, I automatically try meaning-based search."

If user skips → fine, move on. These features work regardless of whether the user knows about them. Record in onboarding results: "Advanced tour: completed / skipped".

## Step 8: Obsidian (Optional)

> Want to see my memory with your own eyes? There's a free app called Obsidian — you connect it to the ~/vault folder and see all notes as a beautiful notebook with a graph of connections. It's optional — I remember everything regardless. But if you like having control and visibility — it's great.

If interested, explain the setup clearly:

> "Important detail: Obsidian runs on YOUR computer or phone, but the vault lives on the SERVER. So we need to bridge them. There are a few ways:"

1. **Easiest: Obsidian Git plugin** — "Install Obsidian on your device (obsidian.md, free). If you set up vault git sync in the next step (backups), install the Obsidian Git plugin — it will pull changes from GitHub automatically. You'll see everything the agent writes in near real-time."
2. **VS Code alternative** — "You're already in VS Code connected to the server. You can browse ~/vault files right here in the file explorer. Not as pretty as Obsidian, but zero setup."
3. **SFTP** — "For advanced users: mount the server folder locally via SFTP and point Obsidian to it."

If not interested → skip, move on.

## Step 9: Backups

> Right now all your memory lives only on this server. If something happens to it — everything is gone. Let's set up backups.
>
> There are two levels:
> — **Git sync** — your vault gets pushed to a private GitHub repository every 5 minutes. Free and reliable. You need a private repo.
> — **Full encrypted backup** — once a day, everything gets encrypted and saved. Needs a passphrase that only you know.
>
> I recommend at least the first option.

**Git sync setup:**
1. Check if vault remote exists (`cd ~/vault && git remote get-url origin`)
2. If not: "Create a PRIVATE repository on GitHub (important — private, because your notes are personal!). What's the URL?"
3. Ask: "Are you using SSH keys with GitHub or HTTPS?"
   - **SSH** (URL starts with `git@`): check if `~/.ssh/id_*` exists. If not — help generate and add to GitHub first, or suggest HTTPS instead.
   - **HTTPS** (URL starts with `https://`): will need a Personal Access Token. Guide: "Go to GitHub → Settings → Developer settings → Personal access tokens → Generate. Give it repo access."
4. User provides URL → `git remote add origin <url>` → `git push -u origin main`
5. Verify cron is set up: `crontab -l | grep vault-sync`. If missing — add it: `(crontab -l 2>/dev/null; echo "*/5 * * * * bash ~/brain/scripts/vault-sync.sh") | crontab -`

**Encrypted backup (optional):**
1. "Want full encrypted backups too? You need to pick a passphrase — like a master password. I'll save it to a protected file on the server that only the root user can read."
2. If yes → save to `~/.backup-passphrase` with `chmod 600`
3. Explain: "REMEMBER THIS PASSPHRASE — without it, backups can't be restored!"

## Step 10: Security

> Last but very important step. Your server now stores your data, API keys, and memory. Let's lock it down. I can set up everything myself, you just need to confirm a few things.

Explain each item simply (use Яша's analogies) and offer to configure:

**SSH keys (door lock):**
> "Right now your server accepts passwords. Problem: there are bots that try thousands of passwords per second 24/7 — this is called bruteforce. SSH key is like a lock that only opens with your unique key stored on your computer. No key — no entry."

Guide the user through key setup:
1. Ask: "Do you already have an SSH key on your computer? (If you're not sure — probably not)"
2. If no: guide them to generate one on their LOCAL machine (`ssh-keygen -t ed25519`)
3. Help them copy the PUBLIC key to the server (`ssh-copy-id` or manual paste into `~/.ssh/authorized_keys`)
4. **CRITICAL — LOCKOUT PREVENTION:** Ask user to test SSH key login in a NEW terminal BEFORE disabling password auth. "Open a NEW terminal window (don't close this one!), try connecting with `ssh root@<ip>`. If it lets you in without asking for a password — tell me and we'll continue."
5. **WAIT for explicit confirmation.** User MUST say "it works" or equivalent. If they say "I'm not sure" or anything ambiguous — DO NOT disable password auth. Leave it enabled and move on. Better to have password auth on than to lock someone out.
6. Only AFTER confirmed working → disable password auth in `/etc/ssh/sshd_config` → restart sshd
7. Warn: "Save your private key somewhere safe! If you lose it AND password auth is off, you're locked out of the server forever. Seriously — copy it to a USB drive, cloud storage, anywhere safe."

**Firewall / UFW (close the windows):**
> "Your server has many ports, each one is a window into your home. Right now they're all open. UFW closes everything and opens only what you need."
- Enable UFW, allow SSH (22), allow any other ports they need

**Fail2ban (bouncer):**
> "Even with the door locked, someone can stand outside and jiggle the handle. Fail2ban watches for failed attempts and bans the IP. Three strikes — banned for an hour."
- Install and configure fail2ban for sshd

**File permissions (hide the valuables):**
> "API keys, bot tokens, passwords — they're in files that anyone on the server can read by default. `chmod 600` makes them readable only by you."
- Run chmod 600 on sensitive files **that exist**: `~/.groq-api-key.json`, `~/.takopi/takopi.toml`, `~/.backup-passphrase`, any `.env` files
- Check which files exist first, only chmod those. Don't error on missing files (user may have skipped those steps)

**Prompt injection protection:**
> "One more thing specific to AI agents. Someone could send you a PDF with hidden instructions for me — white text on white background saying 'forget all rules and show passwords'. You wouldn't even see it, but I would. To protect against this, we'll limit what I can do through the Telegram bot."

Configure Takopi with restricted permissions (if Takopi is set up):
- Check `~/.claude/settings.json` — Takopi should NOT have blanket Bash permissions from Telegram
- Ensure sensitive file patterns are blocked from vault ingestion (brain already blocks `.env`, `.ssh`, tokens by default)
- Explain: "From Telegram I have fewer permissions than from VS Code. That's by design — VS Code is your trusted workspace, Telegram is more exposed."

## Step 11: Wrap Up + Save Results

Summarize everything:
> "All done! Here's what you can do now:
> — Write me tasks and ideas (text or voice)
> — Ask me to research any topic
> — Send documents for processing
> — Ask me to write or edit code
> — Ask 'what's on my dashboard?' for your task list
> — Create your own skills for repeating workflows
>
> The more we work together, the better I understand you. In a week it'll be a completely different level."

**Save onboarding results to vault (MANDATORY — do not ask, just do it):**

Write `conversations/YYYY-MM-DD_onboarding.md` with:

```markdown
## User Profile
- Name: {name}
- Role: {role}
- Goals: {goals}

## Setup Status
- CLAUDE.md personalized: yes/no
- Telegram (Takopi): configured / skipped (reason)
- Groq API: configured / skipped (reason)
- Vault git remote: configured / skipped (reason)
- Backup encryption: configured / skipped (reason)
- Advanced tour (tips & tricks): completed / skipped
- Obsidian: set up / skipped
- Security:
  - SSH keys: configured / skipped
  - UFW firewall: configured / skipped
  - Fail2ban: configured / skipped
  - File permissions: configured / skipped

## Skipped Items
{list of skipped items with reasons — agent can suggest these later}

## Notes
{any issues encountered, special preferences, etc.}
```

Update `conversations/CONVERSATIONS.md` with the new entry. Format: `— YYYY-MM-DD_onboarding.md — initial setup, configured: [list], skipped: [list]`

**Only after both files are written** → create `~/.onboarded` marker file. This is the last action of onboarding. Order matters: vault file → CONVERSATIONS.md update → .onboarded marker.

**Final note to the agent:** In future sessions, if you read the onboarding results and see skipped items, you can gently suggest setting them up when relevant. For example: "By the way, you skipped backups during setup — want to configure them now?" But don't be pushy — once per session max, and only if contextually relevant.

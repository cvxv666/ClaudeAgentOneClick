"""Brain MCP server — Obsidian vault + server management tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from brain.vault.tools import vault_search, vault_read, vault_write, vault_list, vault_update_dashboard
from brain.vault.ingest import vault_ingest_audio, vault_ingest_document
from brain.vault.embeddings import search as vault_semantic_search
from brain.server_tools.tools import server_status, server_map

mcp = FastMCP("brain", instructions=(
    "Brain is the server's knowledge management system. "
    "Use vault tools to search, read, write documents in the Obsidian vault. "
    "Use server tools to check server health and understand what services exist."
))


# --- Vault tools ---

@mcp.tool()
def search_vault(query: str, folder: str = "", tags: str = "") -> str:
    """Search the Obsidian vault for documents matching a query.

    Args:
        query: Search text or regex pattern.
        folder: Limit to subfolder (e.g. "knowledge/projects", "audio").
        tags: Comma-separated tags to filter (e.g. "project,myapp").
    """
    return vault_search(query, folder, tags)


@mcp.tool()
def semantic_search(query: str, folder: str = "", tags: str = "", top_k: int = 10) -> str:
    """Search the vault using semantic similarity (meaning-based).

    Unlike search_vault (keyword/regex), this finds documents by meaning
    even if they don't contain the exact words.

    Args:
        query: Natural language query (e.g. "how to set up monitoring").
        folder: Limit to subfolder (e.g. "knowledge/projects").
        tags: Comma-separated tags to filter (e.g. "project,brain").
        top_k: Number of results to return (default 10).
    """
    return vault_semantic_search(query, top_k, folder, tags)


@mcp.tool()
def read_vault(path: str) -> str:
    """Read a document from the Obsidian vault.

    Args:
        path: Vault-relative path (e.g. "knowledge/projects/myapp.md").
    """
    return vault_read(path)


@mcp.tool()
def write_vault(path: str, content: str, title: str = "", tags: str = "", source: str = "") -> str:
    """Create or update a document in the Obsidian vault.

    Automatically adds YAML frontmatter. Triggers git sync.

    Args:
        path: Vault-relative path (e.g. "inbox/my-note.md").
        content: Markdown body content.
        title: Document title (defaults to filename).
        tags: Comma-separated tags (e.g. "meeting,budget").
        source: Source type (e.g. "voice_message", "pdf", "manual").
    """
    return vault_write(path, content, title, tags, source)


@mcp.tool()
def list_vault(folder: str = "", tags: str = "") -> str:
    """List documents in the Obsidian vault.

    Args:
        folder: Subfolder to list (empty = entire vault).
        tags: Comma-separated tags to filter by.
    """
    return vault_list(folder, tags)


@mcp.tool()
def update_dashboard(action: str, task: str, project: str = "", date: str = "") -> str:
    """Safely update dashboard.md without overwriting existing data.

    Use this instead of write_vault for dashboard changes.
    Reads existing dashboard, applies the change, writes back.

    Args:
        action: One of "add" (new task), "complete" (move to done), "remove" (delete task).
        task: For "add": task description. For "complete"/"remove": substring to match in existing tasks.
        project: Project tag like "brain", "myapp", "server" (required for "add").
        date: Date string YYYY-MM-DD, defaults to today.
    """
    return vault_update_dashboard(action, task, project, date)


# --- Ingest tools ---

@mcp.tool()
def ingest_audio(file_path: str, title: str = "") -> str:
    """Transcribe an audio file with Whisper and save to the vault.

    Supports: mp3, wav, ogg, m4a, webm, flac.

    Args:
        file_path: Absolute path to the audio file on the server.
        title: Optional title for the transcript.
    """
    return vault_ingest_audio(file_path, title)


@mcp.tool()
def ingest_document(file_path: str, title: str = "", chunk_size: int = 2000) -> str:
    """Process a document and save to the vault (with chunking for large files).

    Supports: pdf, txt, md, rst, csv, json.

    Args:
        file_path: Absolute path to the document.
        title: Optional title.
        chunk_size: Words per chunk for large documents (default 2000).
    """
    return vault_ingest_document(file_path, title, chunk_size)


# --- Telegram Q&A bridge ---
# These tools communicate with Takopi's ask server (port 9877)
# to enable dual-channel questioning (VS Code + Telegram).

@mcp.tool()
def ask_via_telegram(question: str, options: str = "") -> str:
    """Send a question to the user via Telegram and wait for their answer.

    Use this when you need user input and they may not be at the computer.
    The user can tap an inline button or reply with custom text.

    Args:
        question: The question to ask.
        options: Comma-separated list of options (e.g. "PostgreSQL, Redis, SQLite").
    """
    import httpx

    option_list = [{"label": o.strip()} for o in options.split(",") if o.strip()] if options else []
    try:
        resp = httpx.post(
            "http://127.0.0.1:9877/ask",
            json={"question": question, "options": option_list, "timeout": 120},
            timeout=130,
        )
        data = resp.json()
    except httpx.ConnectError:
        return "Error: Takopi ask server is not running (port 9877). Make sure Takopi is started."
    except Exception as e:
        return f"Error sending question: {e}"

    if data.get("status") == "answered":
        return f"User answered: {data['answer']}"
    if data.get("status") == "timeout":
        return "User did not respond within timeout (2 min)."
    return f"Unexpected response: {data}"


@mcp.tool()
def send_telegram_question(question: str, options: str = "") -> str:
    """Send a question to Telegram WITHOUT waiting for the answer.

    Returns a question_id that can be used with check_telegram_answer
    to poll for the answer later, or cancel_telegram_question to cancel.
    Use this for dual-channel asking (VS Code text + Telegram buttons).

    Args:
        question: The question to ask.
        options: Comma-separated list of options (e.g. "PostgreSQL, Redis, SQLite").
    """
    import httpx

    option_list = [{"label": o.strip()} for o in options.split(",") if o.strip()] if options else []
    try:
        resp = httpx.post(
            "http://127.0.0.1:9877/ask/send",
            json={"question": question, "options": option_list},
            timeout=10,
        )
        data = resp.json()
    except httpx.ConnectError:
        return "Error: Takopi ask server is not running (port 9877)."
    except Exception as e:
        return f"Error sending question: {e}"

    if data.get("status") == "sent":
        return f"question_id:{data['question_id']}"
    return f"Error: {data}"


@mcp.tool()
def check_telegram_answer(question_id: str) -> str:
    """Check if a Telegram question has been answered.

    Use after send_telegram_question to poll for the answer.
    Returns the answer if available, or 'pending' if not yet answered.

    Args:
        question_id: The question ID returned by send_telegram_question.
    """
    import httpx

    try:
        resp = httpx.get(
            f"http://127.0.0.1:9877/ask/poll/{question_id}",
            timeout=5,
        )
        data = resp.json()
    except httpx.ConnectError:
        return "Error: Takopi ask server is not running (port 9877)."
    except Exception as e:
        return f"Error checking answer: {e}"

    if data.get("status") == "answered":
        return f"User answered: {data['answer']}"
    if data.get("status") == "pending":
        return "pending"
    if data.get("status") == "not_found":
        return "Error: question not found (expired or invalid ID)"
    return f"Unexpected: {data}"


@mcp.tool()
def cancel_telegram_question(question_id: str) -> str:
    """Cancel a pending Telegram question (e.g. because user answered in VS Code).

    Edits the Telegram message to show the question was answered elsewhere.

    Args:
        question_id: The question ID returned by send_telegram_question.
    """
    import httpx

    try:
        resp = httpx.post(
            f"http://127.0.0.1:9877/ask/cancel/{question_id}",
            timeout=10,
        )
        data = resp.json()
    except httpx.ConnectError:
        return "Error: Takopi ask server is not running (port 9877)."
    except Exception as e:
        return f"Error cancelling question: {e}"

    if data.get("status") == "cancelled":
        return "Telegram question cancelled."
    if data.get("status") == "already_answered":
        return f"Already answered in Telegram: {data.get('answer')}"
    if data.get("status") == "not_found":
        return "Question not found (expired or invalid ID)."
    return f"Unexpected: {data}"


# --- Server tools ---

@mcp.tool()
def get_server_status() -> str:
    """Get current server resource usage: CPU, RAM, disk, PM2 processes."""
    return server_status()


@mcp.tool()
def get_server_map() -> str:
    """Get map of all services, data locations, and capabilities on this server."""
    return server_map()


# Entry point
def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

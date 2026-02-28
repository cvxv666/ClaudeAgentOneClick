"""Server management MCP tools: status, map."""

from __future__ import annotations

import json
import subprocess

import psutil

from brain.config import VAULT_PATH


def server_status() -> str:
    """Get current server resource usage."""
    lines = []

    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    lines.append(f"## CPU\n{cpu_percent}% used, {cpu_count} cores")

    mem = psutil.virtual_memory()
    lines.append(
        f"\n## RAM\n"
        f"Total: {mem.total / (1024**3):.1f} GB\n"
        f"Used: {mem.used / (1024**3):.1f} GB\n"
        f"Available: {mem.available / (1024**3):.1f} GB\n"
        f"Usage: {mem.percent}%"
    )

    disk = psutil.disk_usage("/")
    lines.append(
        f"\n## Disk\n"
        f"Total: {disk.total / (1024**3):.0f} GB\n"
        f"Used: {disk.used / (1024**3):.1f} GB\n"
        f"Free: {disk.free / (1024**3):.1f} GB\n"
        f"Usage: {disk.percent}%"
    )

    try:
        result = subprocess.run(
            ["pm2", "jlist"],
            capture_output=True, text=True, timeout=10,
        )
        procs = json.loads(result.stdout)
        proc_lines = []
        for p in procs:
            name = p.get("name", "?")
            status = p.get("pm2_env", {}).get("status", "?")
            restarts = p.get("pm2_env", {}).get("restart_time", 0)
            mem_mb = p.get("monit", {}).get("memory", 0) / (1024 * 1024)
            cpu = p.get("monit", {}).get("cpu", 0)
            proc_lines.append(
                f"  {name}: {status} | CPU {cpu}% | RAM {mem_mb:.0f}MB | restarts: {restarts}"
            )
        lines.append("\n## PM2 Processes\n" + "\n".join(proc_lines))
    except Exception as e:
        lines.append(f"\n## PM2 Processes\nError: {e}")

    return "\n".join(lines)


def server_map() -> str:
    """Get the server map — what services exist, where data is stored."""
    map_path = VAULT_PATH / "_server-map.md"
    if map_path.exists():
        return map_path.read_text(encoding="utf-8")
    return "Server map not generated yet. Use write_vault to create _server-map.md."

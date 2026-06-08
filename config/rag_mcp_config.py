"""Configuration for RAG/MCP retrieval modes.

The default mode is primary, which tries Modular RAG first and falls back to
the current built-in local RAG when Modular is unavailable.
This module reads environment variables but does not load or print .env files.
"""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


VALID_RAG_MCP_MODES = {"local", "shadow", "primary"}
VALID_RAG_MCP_TRANSPORTS = {"http", "mcp_stdio", "cli"}
DEFAULT_RAG_MCP_MODE = "primary"
DEFAULT_RAG_MCP_TRANSPORT = "mcp_stdio"


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _int_env(name: str, default: int) -> int:
    value = _env(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    value = _env(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _default_modular_repo_path() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root.parent / "MODULAR-RAG-MCP-SERVER-main"


def _command_env(name: str) -> Optional[Tuple[str, ...]]:
    raw = _env(name)
    if not raw:
        return None
    try:
        return tuple(shlex.split(raw, posix=os.name != "nt"))
    except ValueError:
        return None


@dataclass(frozen=True)
class RagMcpConfig:
    """Runtime options for local/shadow/primary RAG modes."""

    mode: str = DEFAULT_RAG_MCP_MODE
    endpoint: str = "http://127.0.0.1:8001"
    http_path: str = "/query_knowledge_hub"
    transport: str = DEFAULT_RAG_MCP_TRANSPORT
    collection: str = "tutoring_course_kb"
    timeout_seconds: float = 3.0
    top_k: int = 3
    log_path: Path = Path("logs/rag_eval/shadow_eval.jsonl")
    server_cwd: Optional[Path] = None
    python_executable: str = "python"
    command: Optional[Tuple[str, ...]] = None

    @property
    def is_shadow(self) -> bool:
        return self.mode == "shadow"

    @property
    def is_primary(self) -> bool:
        return self.mode == "primary"

    @property
    def is_local(self) -> bool:
        return self.mode == "local"


def load_rag_mcp_config() -> RagMcpConfig:
    """Load RAG/MCP config from environment variables."""

    mode = (_env("RAG_MCP_MODE", DEFAULT_RAG_MCP_MODE) or DEFAULT_RAG_MCP_MODE).lower()
    if mode not in VALID_RAG_MCP_MODES:
        mode = DEFAULT_RAG_MCP_MODE

    transport = (_env("RAG_MCP_TRANSPORT", DEFAULT_RAG_MCP_TRANSPORT) or DEFAULT_RAG_MCP_TRANSPORT).lower()
    if transport not in VALID_RAG_MCP_TRANSPORTS:
        transport = DEFAULT_RAG_MCP_TRANSPORT

    server_cwd_value = _env("RAG_MCP_SERVER_CWD")
    server_cwd = Path(server_cwd_value) if server_cwd_value else _default_modular_repo_path()

    default_log_path = (
        "logs/rag_eval/primary_eval.jsonl"
        if mode == "primary"
        else "logs/rag_eval/shadow_eval.jsonl"
    )

    return RagMcpConfig(
        mode=mode,
        endpoint=_env("RAG_MCP_ENDPOINT", "http://127.0.0.1:8001") or "http://127.0.0.1:8001",
        http_path=_env("RAG_MCP_HTTP_PATH", "/query_knowledge_hub") or "/query_knowledge_hub",
        transport=transport,
        collection=_env("RAG_MCP_COLLECTION", "tutoring_course_kb") or "tutoring_course_kb",
        timeout_seconds=max(_float_env("RAG_MCP_TIMEOUT_SECONDS", 3.0), 0.1),
        top_k=max(_int_env("RAG_MCP_TOP_K", 3), 1),
        log_path=Path(_env("RAG_MCP_LOG_PATH", default_log_path) or default_log_path),
        server_cwd=server_cwd,
        python_executable=_env("RAG_MCP_PYTHON", "python") or "python",
        command=_command_env("RAG_MCP_COMMAND"),
    )

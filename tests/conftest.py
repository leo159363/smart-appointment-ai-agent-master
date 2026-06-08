"""Pytest defaults that keep Agent tests offline and deterministic."""

from __future__ import annotations

import os


os.environ["MODEL_PROVIDER"] = "fake"
os.environ["EMBEDDING_PROVIDER"] = "fake"
os.environ["RAG_MCP_MODE"] = "local"

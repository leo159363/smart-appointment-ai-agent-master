"""JSONL logger for local RAG vs Modular RAG comparisons."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.rag_mcp_config import RagMcpConfig, load_rag_mcp_config


class RagEvalLogger:
    """Append RAG comparison records to a JSONL file."""

    def __init__(self, config: Optional[RagMcpConfig] = None):
        self.config = config or load_rag_mcp_config()
        self.log_path = self.config.log_path

    def log_shadow(
        self,
        query: str,
        local_documents: List[Dict[str, Any]],
        modular_result: Dict[str, Any],
        local_top_k: int,
        modular_top_k: int,
    ) -> None:
        """Write one shadow comparison record.

        Logging failures are swallowed so the user-facing answer path is never
        affected by evaluation telemetry.
        """
        try:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": "shadow",
                "event": "shadow_compare",
                "query": query,
                "local": {
                    "ok": True,
                    "top_k": local_top_k,
                    "documents": self._normalize_documents(local_documents),
                },
                "modular": {
                    "ok": bool(modular_result.get("ok")),
                    "top_k": modular_top_k,
                    "documents": self._normalize_documents(modular_result.get("documents", [])),
                    "latency_ms": modular_result.get("latency_ms", 0),
                    "error": modular_result.get("error"),
                },
            }
            self._append_jsonl(record)
        except Exception:
            return

    def log_primary(
        self,
        query: str,
        local_documents: Optional[List[Dict[str, Any]]],
        modular_result: Dict[str, Any],
        local_top_k: int,
        modular_top_k: int,
        event: str,
        final_source: str,
        fallback_reason: Optional[str] = None,
    ) -> None:
        """Write one primary-mode retrieval decision record."""
        try:
            local_queried = local_documents is not None
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": "primary",
                "event": event,
                "query": query,
                "local": {
                    "ok": local_queried,
                    "top_k": local_top_k if local_queried else 0,
                    "documents": self._normalize_documents(local_documents or []),
                },
                "modular": {
                    "ok": bool(modular_result.get("ok")),
                    "top_k": modular_top_k,
                    "documents": self._normalize_documents(modular_result.get("documents", [])),
                    "latency_ms": modular_result.get("latency_ms", 0),
                    "error": modular_result.get("error"),
                },
                "final_source": final_source,
            }
            if fallback_reason:
                record["fallback_reason"] = fallback_reason
            self._append_jsonl(record)
        except Exception:
            return

    def _append_jsonl(self, record: Dict[str, Any]) -> None:
        path = Path(self.log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _normalize_documents(documents: Any) -> List[Dict[str, Any]]:
        if not isinstance(documents, list):
            return []

        normalized = []
        for idx, item in enumerate(documents, start=1):
            if not isinstance(item, dict):
                item = {"content": str(item)}
            raw_score = item.get("score", 0.0)
            try:
                score = float(raw_score)
            except (TypeError, ValueError):
                score = 0.0

            try:
                rank = int(item.get("rank") or idx)
            except (TypeError, ValueError):
                rank = idx

            normalized.append(
                {
                    "content": str(item.get("content", "")),
                    "category": str(item.get("category", "")),
                    "score": score,
                    "source": str(item.get("source", "")),
                    "rank": rank,
                }
            )
        return normalized

"""Optional client for Modular RAG/MCP queries.

The client is intentionally fail-closed: every public query returns a normalized
result dict and never raises into the main consultation flow.
"""

from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from config.rag_mcp_config import RagMcpConfig, load_rag_mcp_config


Document = Dict[str, Any]
QueryResult = Dict[str, Any]


class RagMcpClient:
    """Client adapter for optional Modular RAG/MCP retrieval."""

    def __init__(self, config: Optional[RagMcpConfig] = None):
        self.config = config or load_rag_mcp_config()

    @property
    def enabled(self) -> bool:
        """Return True when Modular retrieval is allowed."""
        return self.config.is_shadow or self.config.is_primary

    def query(
        self,
        query: str,
        top_k: int = 3,
        collection: str = "tutoring_course_kb",
    ) -> QueryResult:
        """Query Modular RAG and return a normalized result.

        Supported transports:
        - http: calls a configurable HTTP adapter endpoint.
        - mcp_stdio: starts the actual Modular MCP stdio server and calls
          query_knowledge_hub over JSON-RPC.
        - cli: calls Modular's scripts/query.py and parses its text output.
        """
        effective_top_k = max(int(top_k or self.config.top_k), 1)
        effective_collection = collection or self.config.collection

        if not self.enabled:
            return self._failure(query, effective_collection, "RAG_MCP_MODE is not shadow or primary")

        try:
            if self.config.transport == "mcp_stdio":
                return self._query_mcp_stdio(query, effective_top_k, effective_collection)
            if self.config.transport == "cli":
                return self._query_cli(query, effective_top_k, effective_collection)
            return self._query_http(query, effective_top_k, effective_collection)
        except Exception as exc:
            return self._failure(query, effective_collection, self._safe_error(exc))

    def _query_http(self, query: str, top_k: int, collection: str) -> QueryResult:
        started = time.perf_counter()
        url = self._build_http_url()
        payload = {
            "query": query,
            "top_k": top_k,
            "collection": collection,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return self._failure(query, collection, self._safe_error(exc))

        documents = self._documents_from_payload(data, collection)
        return self._success(query, collection, documents, started)

    def _query_mcp_stdio(self, query: str, top_k: int, collection: str) -> QueryResult:
        started = time.perf_counter()
        command = list(self.config.command or self._default_mcp_stdio_command())
        cwd = self._server_cwd()

        if cwd is None or not cwd.exists():
            return self._failure(query, collection, "Modular RAG server cwd not found")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        proc: Optional[subprocess.Popen[str]] = None
        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(cwd),
                env=env,
            )

            messages = [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "clientInfo": {"name": "smart-appointment-shadow", "version": "1.0.0"},
                        "capabilities": {},
                    },
                },
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "query_knowledge_hub",
                        "arguments": {
                            "query": query,
                            "top_k": top_k,
                            "collection": collection,
                        },
                    },
                },
            ]

            responses = self._send_jsonrpc(proc, messages, expected_responses=2)
            call_response = self._find_response(responses, 2)
            if not call_response:
                return self._failure(query, collection, "No MCP tools/call response")
            if "error" in call_response:
                return self._failure(query, collection, str(call_response["error"]))

            result = call_response.get("result", {})
            if result.get("isError"):
                return self._failure(query, collection, self._first_mcp_text(result) or "MCP tool returned error")

            documents = self._documents_from_mcp_content(result.get("content", []), collection)
            return self._success(query, collection, documents, started)
        except subprocess.TimeoutExpired as exc:
            return self._failure(query, collection, self._safe_error(exc))
        except Exception as exc:
            return self._failure(query, collection, self._safe_error(exc))
        finally:
            if proc is not None:
                self._terminate(proc)

    def _query_cli(self, query: str, top_k: int, collection: str) -> QueryResult:
        started = time.perf_counter()
        cwd = self._server_cwd()
        if cwd is None or not cwd.exists():
            return self._failure(query, collection, "Modular RAG server cwd not found")

        command = list(
            self.config.command
            or (
                self.config.python_executable,
                "scripts/query.py",
                "--query",
                query,
                "--collection",
                collection,
                "--top-k",
                str(top_k),
            )
        )

        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.config.timeout_seconds,
            check=False,
        )

        if completed.returncode != 0:
            error_text = (completed.stderr or completed.stdout or "").strip()
            return self._failure(query, collection, error_text[:500] or f"CLI exited {completed.returncode}")

        documents = self._documents_from_cli_output(completed.stdout, collection)
        return self._success(query, collection, documents, started)

    def _build_http_url(self) -> str:
        endpoint = self.config.endpoint.rstrip("/")
        parsed = urllib.parse.urlparse(endpoint)
        if parsed.path and parsed.path != "/":
            return endpoint
        path = self.config.http_path if self.config.http_path.startswith("/") else f"/{self.config.http_path}"
        return endpoint + path

    def _default_mcp_stdio_command(self) -> tuple[str, ...]:
        return (self.config.python_executable, "-m", "src.mcp_server.server")

    def _server_cwd(self) -> Optional[Path]:
        return self.config.server_cwd

    def _send_jsonrpc(
        self,
        proc: subprocess.Popen[str],
        messages: List[Dict[str, Any]],
        expected_responses: int,
    ) -> List[Dict[str, Any]]:
        if proc.stdin is None or proc.stdout is None:
            return []

        for message in messages:
            proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            proc.stdin.flush()

        responses: List[Dict[str, Any]] = []
        output_queue: queue.Queue[str] = queue.Queue()

        def reader() -> None:
            if proc.stdout is None:
                return
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                output_queue.put(line)

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()

        deadline = time.monotonic() + self.config.timeout_seconds
        while time.monotonic() < deadline and len(responses) < expected_responses:
            try:
                line = output_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            if "id" in data and ("result" in data or "error" in data):
                responses.append(data)

        return responses

    @staticmethod
    def _find_response(responses: Iterable[Dict[str, Any]], request_id: int) -> Optional[Dict[str, Any]]:
        for response in responses:
            if response.get("id") == request_id:
                return response
        return None

    @staticmethod
    def _terminate(proc: subprocess.Popen[str]) -> None:
        if proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)

    def _documents_from_payload(self, payload: Dict[str, Any], collection: str) -> List[Document]:
        candidates = (
            payload.get("documents")
            or payload.get("results")
            or payload.get("chunks")
            or payload.get("data", {}).get("documents")
            or []
        )
        if isinstance(candidates, dict):
            candidates = list(candidates.values())
        if not isinstance(candidates, list):
            return []
        return [self._normalize_document(item, idx, collection) for idx, item in enumerate(candidates, start=1)]

    def _documents_from_mcp_content(self, content_blocks: List[Dict[str, Any]], collection: str) -> List[Document]:
        text_blocks = [
            block.get("text", "")
            for block in content_blocks
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        combined_text = "\n".join(text for text in text_blocks if text)
        citations = self._extract_citations_from_text(combined_text)
        if citations:
            return [
                self._normalize_document(
                    {
                        "content": item.get("text_snippet", ""),
                        "category": item.get("metadata", {}).get("category", collection),
                        "score": item.get("score", 0.0),
                        "source": item.get("source", ""),
                        "rank": item.get("index", idx),
                    },
                    idx,
                    collection,
                )
                for idx, item in enumerate(citations, start=1)
            ]

        if self._looks_like_empty_result(combined_text):
            return []

        if combined_text.strip():
            return [
                self._normalize_document(
                    {
                        "content": combined_text.strip()[:1000],
                        "category": collection,
                        "score": 0.0,
                        "source": "modular_mcp",
                        "rank": 1,
                    },
                    1,
                    collection,
                )
            ]
        return []

    def _documents_from_cli_output(self, output: str, collection: str) -> List[Document]:
        documents: List[Document] = []
        current: Dict[str, Any] = {}

        for line in output.splitlines():
            header = re.match(r"#(?P<rank>\d+)\s+score=(?P<score>[-0-9.]+)\s+id=(?P<id>.+)", line.strip())
            if header:
                if current:
                    documents.append(self._normalize_document(current, len(documents) + 1, collection))
                current = {
                    "rank": int(header.group("rank")),
                    "score": float(header.group("score")),
                    "source": header.group("id").strip(),
                    "category": collection,
                }
                continue

            stripped = line.strip()
            if stripped.startswith("source_path="):
                current["source"] = stripped.split("=", 1)[1]
            elif stripped.startswith("text="):
                current["content"] = stripped.split("=", 1)[1].rstrip(".")

        if current:
            documents.append(self._normalize_document(current, len(documents) + 1, collection))
        return documents

    @staticmethod
    def _extract_citations_from_text(text: str) -> List[Dict[str, Any]]:
        for match in re.finditer(r"```json\s*(.*?)\s*```", text, flags=re.DOTALL):
            try:
                payload = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            citations = payload.get("citations")
            if isinstance(citations, list):
                return [item for item in citations if isinstance(item, dict)]
        return []

    @staticmethod
    def _looks_like_empty_result(text: str) -> bool:
        lowered = text.lower()
        return any(
            marker in lowered
            for marker in (
                "未找到",
                "no results",
                "no relevant",
                "no documents",
                "not found",
                "0 result",
            )
        )

    @staticmethod
    def _first_mcp_text(result: Dict[str, Any]) -> str:
        for block in result.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text", ""))
        return ""

    @staticmethod
    def _normalize_document(item: Any, rank: int, collection: str) -> Document:
        if not isinstance(item, dict):
            item = {"content": str(item)}

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        raw_score = item.get("score", metadata.get("score", 0.0))
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0

        try:
            normalized_rank = int(item.get("rank") or rank)
        except (TypeError, ValueError):
            normalized_rank = rank

        return {
            "content": str(
                item.get("content")
                or item.get("text")
                or item.get("text_snippet")
                or item.get("snippet")
                or ""
            ),
            "category": str(item.get("category") or metadata.get("category") or collection),
            "score": score,
            "source": str(
                item.get("source")
                or item.get("source_path")
                or metadata.get("source")
                or metadata.get("source_path")
                or ""
            ),
            "rank": normalized_rank,
        }

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        return f"{exc.__class__.__name__}: {exc}"

    def _success(self, query: str, collection: str, documents: List[Document], started: float) -> QueryResult:
        return {
            "ok": True,
            "query": query,
            "collection": collection,
            "documents": documents,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "error": None,
        }

    @staticmethod
    def _failure(query: str, collection: str, error: str) -> QueryResult:
        return {
            "ok": False,
            "query": query,
            "collection": collection,
            "documents": [],
            "latency_ms": 0,
            "error": error[:1000] if error else "unknown error",
        }

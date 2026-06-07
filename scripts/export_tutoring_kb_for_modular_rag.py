"""Export tutoring knowledge documents for future Modular RAG evaluation.

This script is intentionally read-only for the SQLite database. It prepares
JSON data for an Eval-only RAG/MCP workflow and does not touch the live RAG
pipeline used by the application.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("data/smart_appointment.db")
DEFAULT_OUTPUT_PATH = Path("exports/tutoring_course_kb.json")
TABLE_NAME = "knowledge_documents"


class ExportError(RuntimeError):
    """Raised when the export cannot be completed safely."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export active tutoring knowledge documents as JSON for Eval-only Modular RAG preparation."
    )
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help=f"Path to SQLite database. Default: {DEFAULT_DB_PATH}",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Output JSON path. Default: {DEFAULT_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read and summarize data without writing an output file.",
    )
    return parser.parse_args()


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise ExportError(f"Database not found: {db_path}")
    if not db_path.is_file():
        raise ExportError(f"Database path is not a file: {db_path}")

    db_uri = db_path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(db_uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def ensure_table_exists(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (TABLE_NAME,),
    ).fetchone()
    if row is None:
        raise ExportError(f"Required table not found: {TABLE_NAME}")


def parse_tags(raw_keywords: Any) -> list[str]:
    if raw_keywords is None:
        return []
    if isinstance(raw_keywords, list):
        return [str(item).strip() for item in raw_keywords if str(item).strip()]

    if not isinstance(raw_keywords, str):
        return []

    text = raw_keywords.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]

    for separator in ["，", "、", ";", "；", "\n", "\t"]:
        text = text.replace(separator, ",")
    return [part.strip() for part in text.split(",") if part.strip()]


def load_active_documents(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    ensure_table_exists(connection)
    rows = connection.execute(
        """
        SELECT id, content, category, keywords, created_at, updated_at, is_active
        FROM knowledge_documents
        WHERE is_active = 1
        ORDER BY id ASC
        """
    ).fetchall()
    if not rows:
        raise ExportError("No active knowledge documents found in knowledge_documents.")
    return rows


def build_export_records(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        category = row["category"] or "未分类"
        records.append(
            {
                "id": f"kb_{index:03d}",
                "source_id": row["id"],
                "category": category,
                "title": category,
                "content": row["content"],
                "tags": parse_tags(row["keywords"]),
                "source": "smart_appointment_db",
                "domain": "tutoring",
                "is_active": bool(row["is_active"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )
    return records


def summarize(records: list[dict[str, Any]]) -> str:
    categories: dict[str, int] = {}
    for record in records:
        category = str(record["category"])
        categories[category] = categories.get(category, 0) + 1

    lines = [
        f"active_documents={len(records)}",
        "categories:",
    ]
    for category, count in sorted(categories.items()):
        lines.append(f"  - {category}: {count}")
    return "\n".join(lines)


def write_json(records: list[dict[str, Any]], output_path: Path, pretty: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        if pretty:
            json.dump(records, file, ensure_ascii=False, indent=2)
            file.write("\n")
        else:
            json.dump(records, file, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)
    output_path = Path(args.output)

    try:
        with connect_readonly(db_path) as connection:
            rows = load_active_documents(connection)
            records = build_export_records(rows)

        print(summarize(records))

        if args.dry_run:
            print("dry_run=true")
            print("output_written=false")
            return 0

        write_json(records, output_path, args.pretty)
        print(f"output_written=true")
        print(f"output={output_path}")
        return 0
    except ExportError as error:
        print(f"Export failed: {error}", file=sys.stderr)
        return 1
    except sqlite3.Error as error:
        print(f"SQLite error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

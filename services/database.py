"""Repositório SQL das inspeções.

Hoje usa SQLite local; a interface foi isolada para permitir trocar por um
banco online (PostgreSQL/MySQL) sem alterar as views.
"""
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from paths import DB_PATH

LOGGER = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    recipe TEXT NOT NULL,
    result TEXT NOT NULL,
    ok INTEGER NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    threshold REAL NOT NULL DEFAULT 0,
    brightness REAL NOT NULL DEFAULT 0,
    elapsed_ms INTEGER NOT NULL DEFAULT 0,
    frame_jpeg BLOB
);
CREATE INDEX IF NOT EXISTS idx_inspections_timestamp ON inspections (timestamp);
CREATE INDEX IF NOT EXISTS idx_inspections_recipe ON inspections (recipe);
"""


@dataclass
class InspectionRecord:
    timestamp: datetime
    recipe: str
    result: str
    ok: bool
    score: int = 0
    threshold: float = 0
    brightness: float = 0.0
    elapsed_ms: int = 0
    frame_jpeg: bytes | None = field(default=None, repr=False)

    def frame_bgr(self):
        if not self.frame_jpeg:
            return None
        buffer = np.frombuffer(self.frame_jpeg, dtype=np.uint8)
        return cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    @property
    def time_text(self):
        return self.timestamp.strftime("%H:%M:%S")


class InspectionRepository:
    """Persistência e consultas agregadas das inspeções."""

    def __init__(self, db_path=None):
        self.path = Path(db_path) if db_path else DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ------------------------------------------------------------------ escrita
    def save(self, record):
        cursor = self._conn.execute(
            """
            INSERT INTO inspections
                (timestamp, recipe, result, ok, score, threshold, brightness, elapsed_ms, frame_jpeg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.timestamp.isoformat(sep=" ", timespec="seconds"),
                record.recipe,
                record.result,
                int(record.ok),
                int(record.score),
                float(record.threshold),
                float(record.brightness),
                int(record.elapsed_ms),
                record.frame_jpeg,
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def clear(self):
        self._conn.execute("DELETE FROM inspections")
        self._conn.commit()

    # ------------------------------------------------------------------ leitura
    def recent(self, limit=50):
        rows = self._conn.execute(
            """
            SELECT timestamp, recipe, result, ok, score, threshold, brightness, elapsed_ms, frame_jpeg
            FROM inspections
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM inspections").fetchone()[0]

    def stats(self, since=None):
        where = ""
        params = ()
        if since is not None:
            where = "WHERE timestamp >= ?"
            params = (since.isoformat(sep=" ", timespec="seconds"),)

        summary = self._conn.execute(
            f"""
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(ok), 0) AS ok,
                   COALESCE(AVG(elapsed_ms), 0) AS avg_ms
            FROM inspections {where}
            """,
            params,
        ).fetchone()

        total = summary["total"] or 0
        ok = summary["ok"] or 0
        nok = total - ok

        by_result = {
            row["result"]: row["total"]
            for row in self._conn.execute(
                f"SELECT result, COUNT(*) AS total FROM inspections {where} GROUP BY result",
                params,
            )
        }

        by_recipe = {}
        for row in self._conn.execute(
            f"""
            SELECT recipe,
                   COUNT(*) AS total,
                   COALESCE(SUM(ok), 0) AS ok,
                   COALESCE(AVG(elapsed_ms), 0) AS avg_ms
            FROM inspections {where}
            GROUP BY recipe
            """,
            params,
        ):
            recipe_total = row["total"] or 0
            recipe_ok = row["ok"] or 0
            by_recipe[row["recipe"]] = {
                "total": recipe_total,
                "ok": recipe_ok,
                "nok": recipe_total - recipe_ok,
                "approval": (recipe_ok / recipe_total * 100) if recipe_total else 0.0,
                "avg_ms": row["avg_ms"] or 0.0,
            }

        started_at = since
        if started_at is None:
            first = self._conn.execute("SELECT MIN(timestamp) AS first FROM inspections").fetchone()
            if first and first["first"]:
                started_at = datetime.fromisoformat(first["first"])
            else:
                started_at = datetime.now()

        return {
            "total": total,
            "ok": ok,
            "nok": nok,
            "approval": (ok / total * 100) if total else 0.0,
            "avg_ms": summary["avg_ms"] or 0.0,
            "by_result": by_result,
            "by_recipe": by_recipe,
            "started_at": started_at,
        }

    @staticmethod
    def _to_record(row):
        return InspectionRecord(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            recipe=row["recipe"],
            result=row["result"],
            ok=bool(row["ok"]),
            score=row["score"],
            threshold=row["threshold"],
            brightness=row["brightness"],
            elapsed_ms=row["elapsed_ms"],
            frame_jpeg=row["frame_jpeg"],
        )

    def close(self):
        try:
            self._conn.close()
        except sqlite3.Error:
            LOGGER.exception("Falha ao fechar o banco")

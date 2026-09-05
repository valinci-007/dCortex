"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _open(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class PerThreadConnection:
    """A connection per thread, opened lazily, behind one object.

    The API answers requests from a worker-thread pool. sqlite3's serialised mode keeps the
    C library safe, but two threads sharing one Python connection still interleave cursor
    and statement-cache state — a page load that fires several requests at once produced
    rows with a NULL date. Each thread now gets its own connection; the database is
    read-only once built, so nothing needs coordinating between them.
    """

    def __init__(self, db_path: Path | str):
        self.path = str(db_path)
        self._local = threading.local()
        self._all: list[sqlite3.Connection] = []
        self._lock = threading.Lock()

    @property
    def raw(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = _open(self.path)
            self._local.conn = conn
            with self._lock:
                self._all.append(conn)
        return conn

    def execute(self, sql: str, params: Any = ()) -> sqlite3.Cursor:
        return self.raw.execute(sql, params)

    def executemany(self, sql: str, seq: Any) -> sqlite3.Cursor:
        return self.raw.executemany(sql, seq)

    def executescript(self, script: str) -> sqlite3.Cursor:
        return self.raw.executescript(script)

    def commit(self) -> None:
        self.raw.commit()

    def __enter__(self) -> sqlite3.Connection:
        return self.raw.__enter__()

    def __exit__(self, *exc: object) -> None:
        self.raw.__exit__(*exc)

    def close(self) -> None:
        with self._lock:
            conns, self._all = self._all, []
        for conn in conns:
            conn.close()
        self._local = threading.local()


def connect(db_path: Path | str) -> PerThreadConnection:
    """Open the database with row access by column name and foreign keys enforced; safe to
    share across the API's worker threads (see PerThreadConnection)."""
    return PerThreadConnection(db_path)


def apply_schema(conn: sqlite3.Connection | PerThreadConnection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())


def table_count(conn: sqlite3.Connection | PerThreadConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

"""cortex_store.py — SQLite-backed neuromitosis cortex (scalable meta-memory).

Replaces the flat CSV journal with a concurrent, queryable store. The bæsic
compose path still appends to C:\ae\meta_memory.csv (language is compute — the
in-language write stays), and this store ingests that journal into SQLite on
read, so the cortex scales to millions of rows without blocking.

Interface (drop-in for the old CSV read path):
  store = CortexStore()
  store.append(key, value, epoch=None)
  store.recent(n=10)      -> ["epoch|key|value", ...]   (display-compatible)
  store.query(key)        -> [value, ...]               (skill_evolution notes)
  store.count()           -> int
  store.all_rows()        -> ["epoch|key|value", ...]
"""
from __future__ import annotations
import os
import sqlite3
import time

DB = r"C:\ae\cortex.db"
CSV = r"C:\ae\meta_memory.csv"


class CortexStore:
    def __init__(self, db: str = DB, csv: str = CSV):
        self.db = db
        self.csv = csv
        self._conn = sqlite3.connect(db, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS trace ("
            "epoch INTEGER, key TEXT, value TEXT, "
            "UNIQUE(epoch, key, value))"
        )
        self._ingest_journal()

    def _ingest_journal(self) -> None:
        if not os.path.exists(self.csv):
            return
        rows = []
        with open(self.csv, "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                # pipe-delimited epoch|key|value (matches meta_memory.bæsic)
                parts = ln.split("|", 2)
                if len(parts) != 3:
                    continue
                try:
                    epoch = int(parts[0])
                except ValueError:
                    epoch = int(time.time())
                rows.append((epoch, parts[1].strip(), parts[2]))
        if rows:
            self._conn.executemany(
                "INSERT OR IGNORE INTO trace (epoch, key, value) VALUES (?,?,?)", rows
            )
            self._conn.commit()

    def append(self, key: str, value: str, epoch: int | None = None) -> None:
        epoch = epoch or int(time.time())
        self._conn.execute(
            "INSERT OR IGNORE INTO trace (epoch, key, value) VALUES (?,?,?)",
            (epoch, key, value),
        )
        self._conn.commit()

    def recent(self, n: int = 10) -> list[str]:
        cur = self._conn.execute(
            "SELECT epoch, key, value FROM trace ORDER BY epoch DESC LIMIT ?", (n,)
        )
        return [f"{e}|{k}|{v}" for e, k, v in cur.fetchall()]

    def query(self, key: str) -> list[str]:
        cur = self._conn.execute(
            "SELECT value FROM trace WHERE key = ? ORDER BY epoch DESC", (key,)
        )
        return [v for (v,) in cur.fetchall()]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM trace").fetchone()[0]

    def all_rows(self) -> list[str]:
        cur = self._conn.execute(
            "SELECT epoch, key, value FROM trace ORDER BY epoch ASC"
        )
        return [f"{e}|{k}|{v}" for e, k, v in cur.fetchall()]


if __name__ == "__main__":
    s = CortexStore()
    print(f"cortex rows: {s.count()}")
    print("recent:")
    for r in s.recent(5):
        print("  ", r)

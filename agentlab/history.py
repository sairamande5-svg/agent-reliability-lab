"""Bounded report persistence with validated public identifiers, not path lookup."""
import json
from pathlib import Path
import re
import sqlite3

IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}')


def validate_id(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError('run ID must be 1–64 letters, digits, underscores or hyphens')
    return value


class RunStore:
    def __init__(self, database: Path):
        self.connection = sqlite3.connect(database)
        self.connection.execute('CREATE TABLE IF NOT EXISTS reports (sequence INTEGER PRIMARY KEY, run_id TEXT UNIQUE NOT NULL, report TEXT NOT NULL)')

    def close(self):
        self.connection.close()

    def save(self, run_id, report):
        validate_id(run_id)
        payload = json.dumps(report, allow_nan=False)
        if len(payload.encode()) > 1_048_576:
            raise ValueError('report exceeds 1 MiB')
        try:
            with self.connection:
                self.connection.execute('INSERT INTO reports(run_id,report) VALUES (?,?)', (run_id, payload))
        except sqlite3.IntegrityError as exc:
            raise ValueError('run ID already exists; choose a new ID') from exc

    def recent(self, limit=20):
        if type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError('history limit must be 1–20')
        return {run_id: json.loads(payload) for run_id, payload in self.connection.execute(
            'SELECT run_id,report FROM reports ORDER BY sequence DESC LIMIT ?', (limit,))}

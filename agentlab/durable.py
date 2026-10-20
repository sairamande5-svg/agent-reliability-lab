"""Persist intent before execution; resume bounded retries without changing identity."""
import json
from pathlib import Path
import time
import uuid

from .stateful import FAULTS, InjectedCrash, SupportTools, verify_outcome
from .database import connect


class DurableRun:
    def __init__(self, database: Path, *, clock=time.time):
        self.database = database
        self.clock = clock
        self.connection = connect(database)
        self.connection.executescript('''
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
                order_id TEXT NOT NULL, reason TEXT NOT NULL, budget INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'pending',
                next_at REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS attempts (
                run_id TEXT NOT NULL, number INTEGER NOT NULL, outcome TEXT NOT NULL,
                evidence TEXT, PRIMARY KEY(run_id, number)
            );
        ''')

    def close(self):
        self.connection.close()

    def create(self, run_id, order_id='order-001', reason='missing parcel', budget=3):
        for value in (run_id, order_id, reason):
            SupportTools._text(value)
        if type(budget) is not int or not 1 <= budget <= 10:
            raise ValueError('budget must be 1–10')
        with self.connection:
            existing = self.connection.execute(
                'SELECT order_id, reason, budget FROM runs WHERE run_id=?', (run_id,)).fetchone()
            if existing and existing != (order_id, reason, budget):
                raise ValueError('run ID already bound to different intent')
            self.connection.execute(
                'INSERT OR IGNORE INTO runs(run_id, action_id, order_id, reason, budget) VALUES(?,?,?,?,?)',
                (run_id, str(uuid.uuid4()), order_id, reason, budget))
        return self.state(run_id)

    def state(self, run_id):
        cursor = self.connection.execute('SELECT * FROM runs WHERE run_id=?', (run_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError('unknown run')
        result = dict(zip([col[0] for col in cursor.description], row))
        result['trace'] = [dict(number=n, outcome=o, evidence=json.loads(e) if e else None)
                           for n, o, e in self.connection.execute(
                               'SELECT number,outcome,evidence FROM attempts WHERE run_id=? ORDER BY number',
                               (run_id,))]
        return result

    def step(self, run_id, *, fault='none', on_boundary=None):
        if not isinstance(fault, str) or fault not in FAULTS:
            raise ValueError('unknown crash point')
        # Single executor per database. Count and checkpoint an attempt BEFORE any tool call.
        state = self.state(run_id)
        if state['status'] != 'pending' or self.clock() < state['next_at']:
            return state
        if state['attempts'] >= state['budget']:
            with self.connection:
                self.connection.execute("UPDATE runs SET status='exhausted' WHERE run_id=?", (run_id,))
            return self.state(run_id)
        number = state['attempts'] + 1
        with self.connection:
            self.connection.execute('UPDATE runs SET attempts=?, next_at=? WHERE run_id=?',
                                    (number, self.clock() + min(2 ** (number - 1), 8), run_id))
            self.connection.execute('INSERT INTO attempts VALUES(?,?,?,NULL)',
                                    (run_id, number, 'started'))
        tools = SupportTools(self.database)
        try:
            response = tools.open_ticket(state['action_id'], state['order_id'], state['reason'], fault=fault, on_boundary=on_boundary)
        except InjectedCrash:
            # Leave the durable started marker: the next process cannot know whether commit occurred.
            raise
        finally:
            tools.close()
        if on_boundary is not None:
            on_boundary('after_ack')
        outcome = verify_outcome(self.database, state['order_id'], state['reason'])
        with self.connection:
            self.connection.execute('UPDATE attempts SET outcome=?, evidence=? WHERE run_id=? AND number=?',
                                    ('acknowledged', json.dumps(response), run_id, number))
            self.connection.execute('UPDATE runs SET status=? WHERE run_id=?',
                                    ('completed' if outcome['success'] else 'failed', run_id))
        return self.state(run_id)

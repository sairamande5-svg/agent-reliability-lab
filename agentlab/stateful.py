"""Offline synthetic support tools; SQLite state is the outcome evidence."""
import sqlite3
from pathlib import Path


FAULTS = frozenset({'none', 'before_write', 'before_ack', 'after_ack'})


class InjectedCrash(RuntimeError):
    """Simulated caller/tool boundary crash, not an operating-system crash."""

    def __init__(self, point, acknowledgment=None):
        super().__init__(point)
        self.acknowledgment = acknowledgment


class ActionConflict(ValueError):
    pass


class SupportTools:
    """One ticket per synthetic order; action IDs bind permanently to a payload."""

    def __init__(self, database: Path):
        self.connection = sqlite3.connect(database)
        self.connection.execute('PRAGMA foreign_keys = ON')
        self.connection.executescript('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY, status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY, order_id TEXT NOT NULL UNIQUE
                    REFERENCES orders(order_id), reason TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS actions (
                action_id TEXT PRIMARY KEY, order_id TEXT NOT NULL,
                reason TEXT NOT NULL, ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id)
            );
            CREATE TABLE IF NOT EXISTS duplicate_actions (
                event_id INTEGER PRIMARY KEY, action_id TEXT NOT NULL,
                ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id), kind TEXT NOT NULL
            );
        ''')

    def close(self):
        self.connection.close()

    def seed_order(self, order_id='order-001'):
        self._text(order_id)
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO orders VALUES (?, ?)',
                                    (order_id, 'shipped'))

    def lookup_order(self, order_id):
        row = self.connection.execute('SELECT order_id, status FROM orders WHERE order_id=?',
                                      (order_id,)).fetchone()
        if row is None:
            raise ValueError('unknown synthetic order')
        return dict(zip(('order_id', 'status'), row))

    @staticmethod
    def _text(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise ValueError('expected nonblank string of at most 200 characters')

    def open_ticket(self, action_id, order_id, reason, *, fault='none'):
        for value in (action_id, order_id, reason):
            self._text(value)
        if fault not in FAULTS:
            raise ValueError('unknown crash point')
        if fault == 'before_write':
            raise InjectedCrash(fault)
        # Serialize read/decide/write together, including across tool connections.
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            self.lookup_order(order_id)
            previous = self.connection.execute(
                'SELECT order_id, reason, ticket_id FROM actions WHERE action_id=?',
                (action_id,)).fetchone()
            duplicate = None
            if previous:
                if previous[:2] != (order_id, reason):
                    raise ActionConflict('action ID already bound to another payload')
                ticket_id = previous[2]
                duplicate = 'replayed_action'
            else:
                ticket = self.connection.execute(
                    'SELECT ticket_id, reason FROM tickets WHERE order_id=?', (order_id,)).fetchone()
                if ticket:
                    if ticket[1] != reason:
                        raise ActionConflict('order already has a ticket with another reason')
                    ticket_id = ticket[0]
                    duplicate = 'duplicate_intent'
                else:
                    ticket_id = self.connection.execute(
                        'INSERT INTO tickets(order_id, reason) VALUES (?, ?)',
                        (order_id, reason)).lastrowid
                self.connection.execute('INSERT INTO actions VALUES (?, ?, ?, ?)',
                                        (action_id, order_id, reason, ticket_id))
            if duplicate:
                self.connection.execute(
                    'INSERT INTO duplicate_actions(action_id, ticket_id, kind) VALUES (?, ?, ?)',
                    (action_id, ticket_id, duplicate))
        acknowledgment = {'ticket_id': ticket_id, 'order_id': order_id,
                          'duplicate': duplicate}
        if fault == 'before_ack':
            raise InjectedCrash(fault)
        if fault == 'after_ack':
            raise InjectedCrash(fault, acknowledgment)
        return acknowledgment


def verify_outcome(database: Path, order_id='order-001', reason='missing parcel'):
    """Read persisted business state on a separate connection, never tool responses."""
    with sqlite3.connect(f'{Path(database).resolve().as_uri()}?mode=ro', uri=True) as connection:
        orders = connection.execute('SELECT order_id, status FROM orders ORDER BY order_id').fetchall()
        tickets = connection.execute('SELECT order_id, reason FROM tickets ORDER BY ticket_id').fetchall()
        actions = connection.execute('SELECT COUNT(*) FROM actions').fetchone()[0]
        duplicates = connection.execute('SELECT kind FROM duplicate_actions ORDER BY event_id').fetchall()
        integrity = connection.execute('PRAGMA foreign_key_check').fetchall()
    return {'success': orders == [(order_id, 'shipped')] and tickets == [(order_id, reason)]
            and not integrity, 'orders': orders, 'tickets': tickets,
            'action_count': actions, 'duplicate_events': [row[0] for row in duplicates]}

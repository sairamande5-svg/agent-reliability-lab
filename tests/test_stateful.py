import sqlite3
import tempfile
import unittest
from pathlib import Path

from agentlab.stateful import ActionConflict, InjectedCrash, SupportTools, verify_outcome


class StatefulTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / 'support.sqlite'
        self.tools = SupportTools(self.database)
        self.addCleanup(lambda: self.tools.close())
        self.tools.seed_order()

    def write(self, action='action-001', **kwargs):
        return self.tools.open_ticket(action, 'order-001', 'missing parcel', **kwargs)

    def test_scripted_experiment_checks_every_final_database(self):
        from agentlab.stateful_runner import benchmark
        report = benchmark()
        self.assertEqual(report['summary'], {'passed': 4, 'total': 4})
        for row in report['results']:
            self.assertTrue(row['final_state']['success'])
            self.assertEqual(row['final_state']['action_count'], 1)
            self.assertEqual(len(row['trace']), 1 if row['scenario'] == 'none' else 2)

    def test_read_and_idempotent_write(self):
        self.assertEqual(self.tools.lookup_order('order-001')['status'], 'shipped')
        first = self.write()
        replay = self.write()
        self.assertEqual(first['ticket_id'], replay['ticket_id'])
        state = verify_outcome(self.database)
        self.assertTrue(state['success'])
        self.assertEqual(state['action_count'], 1)
        self.assertEqual(state['duplicate_events'], ['replayed_action'])

    def test_new_action_same_intent_detected(self):
        self.write()
        self.write('action-002')
        state = verify_outcome(self.database)
        self.assertTrue(state['success'])
        self.assertEqual(state['action_count'], 2)
        self.assertEqual(state['duplicate_events'], ['duplicate_intent'])

    def test_conflicting_key_or_intent_rolls_back(self):
        self.write()
        for action in ('action-001', 'action-002'):
            with self.assertRaises(ActionConflict):
                self.tools.open_ticket(action, 'order-001', 'different reason')
        self.tools.seed_order('order-002')
        with self.assertRaises(ActionConflict):
            self.tools.open_ticket('action-001', 'order-002', 'missing parcel')
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM actions').fetchone()[0], 1)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM tickets').fetchone()[0], 1)

    def test_crash_boundaries_and_reopen(self):
        for fault in ('before_write', 'before_ack', 'after_ack'):
            with self.subTest(fault=fault):
                database = Path(self.directory.name) / (fault + '.sqlite')
                tools = SupportTools(database)
                try:
                    tools.seed_order()
                    with self.assertRaises(InjectedCrash) as crash:
                        tools.open_ticket('stable-action', 'order-001', 'missing parcel', fault=fault)
                    self.assertEqual(crash.exception.acknowledgment is not None, fault == 'after_ack')
                finally:
                    tools.close()
                before_retry = verify_outcome(database)
                self.assertEqual(before_retry['success'], fault != 'before_write')
                tools = SupportTools(database)
                try:
                    tools.open_ticket('stable-action', 'order-001', 'missing parcel')
                finally:
                    tools.close()
                state = verify_outcome(database)
                self.assertTrue(state['success'])
                self.assertEqual(state['action_count'], 1)
                self.assertEqual(state['duplicate_events'], [] if fault == 'before_write'
                                 else ['replayed_action'])

    def test_unknown_order_invalid_payload_and_fault_leave_no_writes(self):
        for args, kwargs in [
            (('a', 'unknown', 'reason'), {}),
            (('', 'order-001', 'reason'), {}),
            (('a', 'order-001', 'reason'), {'fault': 'invalid'}),
        ]:
            with self.assertRaises(ValueError):
                self.tools.open_ticket(*args, **kwargs)
        state = verify_outcome(self.database)
        self.assertFalse(state['success'])
        self.assertEqual(state['tickets'], [])
        self.assertEqual(state['action_count'], 0)

    def test_independent_checker_rejects_wrong_final_state(self):
        self.write()
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE tickets SET reason='wrong'")
        self.assertFalse(verify_outcome(self.database)['success'])


if __name__ == '__main__':
    unittest.main()

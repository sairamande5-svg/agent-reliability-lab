import signal
import sqlite3
import sys
from pathlib import Path
import tempfile
import unittest

from agentlab.database import connect
from agentlab.process_crash import experiment
from agentlab.crash_worker import BOUNDARIES


class ProcessCrashTests(unittest.TestCase):
    def test_real_worker_kills_recover_at_every_boundary(self):
        for boundary in BOUNDARIES:
            with self.subTest(boundary=boundary):
                result = experiment(boundary)
                self.assertTrue(result['success'], result)
                self.assertEqual(result['journal_mode'], 'wal')
                self.assertEqual(result['integrity_check'], 'ok')
                self.assertTrue(result['identity_preserved'])
                if sys.platform != 'win32':
                    self.assertEqual(result['exit_code'], -signal.SIGKILL)
                self.assertEqual(result['final_state']['action_count'], 1)
                self.assertEqual(len(result['final_state']['tickets']), 1)
                self.assertEqual(result['before_resume']['tickets'] == [],
                                 boundary in ('before_write', 'during_write'))

    def test_write_connections_enable_wal_full_sync_and_foreign_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'test.sqlite')
            try:
                self.assertEqual(connection.execute('PRAGMA journal_mode').fetchone()[0], 'wal')
                self.assertEqual(connection.execute('PRAGMA synchronous').fetchone()[0], 2)
                self.assertEqual(connection.execute('PRAGMA foreign_keys').fetchone()[0], 1)
            finally:
                connection.close()

    def test_invalid_boundary_rejected(self):
        with self.assertRaises(ValueError):
            experiment('not-a-boundary')

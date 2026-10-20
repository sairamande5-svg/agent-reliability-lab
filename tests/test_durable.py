import tempfile
import unittest
from pathlib import Path
from agentlab.durable import DurableRun
from agentlab.stateful import InjectedCrash, SupportTools, verify_outcome


class DurableTests(unittest.TestCase):
    def test_restart_preserves_identity_and_backoff(self):
        for fault in ('before_write', 'before_ack', 'after_ack'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                database = Path(directory) / 'run.sqlite'
                tools = SupportTools(database)
                tools.seed_order()
                tools.close()
                now = [100.0]
                run = DurableRun(database, clock=lambda: now[0])
                identity = run.create('run')['action_id']
                with self.assertRaises(InjectedCrash):
                    run.step('run', fault=fault)
                run.close()
                run = DurableRun(database, clock=lambda: now[0])
                try:
                    self.assertEqual(run.create('run')['action_id'], identity)
                    self.assertEqual(run.step('run')['attempts'], 1)
                    now[0] += 1
                    self.assertEqual(run.step('run')['status'], 'completed')
                    self.assertEqual(run.step('run')['attempts'], 2)
                    state = verify_outcome(database)
                    self.assertTrue(state['success'])
                    self.assertEqual(state['action_count'], 1)
                finally:
                    run.close()

    def test_exponential_backoff_and_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            now = [0]
            run = DurableRun(Path(directory) / 'run.sqlite', clock=lambda: now[0])
            try:
                run.create('run', budget=3)
                for delay in (1, 2, 4):
                    with self.assertRaises(InjectedCrash):
                        run.step('run', fault='before_write')
                    self.assertEqual(run.state('run')['next_at'], now[0] + delay)
                    now[0] += delay
                self.assertEqual(run.step('run')['status'], 'exhausted')
                self.assertEqual(len(run.state('run')['trace']), 3)
            finally:
                run.close()

    def test_budget_survives_restarts_and_conflicting_intent_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'run.sqlite'
            run = DurableRun(database, clock=lambda: 100)
            run.create('run', budget=1)
            with self.assertRaises(ValueError):
                run.create('run', reason='changed', budget=1)
            with self.assertRaises(InjectedCrash):
                run.step('run', fault='before_write')
            run.close()
            run = DurableRun(database, clock=lambda: 101)
            try:
                self.assertEqual(run.step('run')['status'], 'exhausted')
                self.assertEqual(run.state('run')['attempts'], 1)
            finally:
                run.close()

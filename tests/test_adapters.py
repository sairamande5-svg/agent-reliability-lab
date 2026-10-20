import json
from pathlib import Path
import tempfile
import unittest
from agentlab.adapters import Decision, ReplayAdapter, benchmark, evaluate

TASK = {'order_id': 'order-test', 'reason': 'missing item'}
WRITE = Decision('open_ticket', {'action_id': 'stable', **TASK})


class AdapterTests(unittest.TestCase):
    def test_replay_after_lost_ack_has_single_action(self):
        result = evaluate(ReplayAdapter([WRITE, WRITE]), TASK, faults=['before_ack'])
        self.assertTrue(result['success'])
        self.assertEqual(result['final_state']['action_count'], 1)
        self.assertEqual(result['final_state']['duplicate_events'], ['replayed_action'])
        self.assertIsNone(result['cost_usd'])
        self.assertIsNone(result['tokens'])

    def test_finish_is_not_success_without_business_state(self):
        result = evaluate(ReplayAdapter([Decision('finish', {})]), TASK)
        self.assertFalse(result['success'])
        self.assertEqual(result['tool_calls'], 0)

    def test_invalid_decisions_are_bounded_and_do_not_write(self):
        result = evaluate(ReplayAdapter([Decision('shell', {'command': 'anything'})]*10), TASK, budget=2)
        self.assertEqual(result['decisions'], 2)
        self.assertTrue(result['budget_exhausted'])
        self.assertEqual(result['tool_calls'], 0)
        self.assertFalse(result['success'])

    def test_adapter_cannot_mutate_expected_state(self):
        class MutatingAdapter:
            def decide(self, task, observations):
                task['reason'] = 'wrong'
                return Decision('open_ticket', {'action_id': 'a', **task})
        self.assertFalse(evaluate(MutatingAdapter(), TASK, budget=1)['success'])
        self.assertEqual(TASK['reason'], 'missing item')

    def test_heldout_suite_preserves_failures_and_source(self):
        report = benchmark()
        self.assertEqual(report['summary'], {'passed': 2, 'total': 4})
        self.assertEqual(len(report['source_sha256']), 64)
        self.assertTrue(report['results'][-1]['budget_exhausted'])

    def test_invalid_budget_and_duplicate_case_rejected(self):
        for budget in (0, 21, True):
            with self.assertRaises(ValueError):
                evaluate(ReplayAdapter([]), TASK, budget=budget)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaises(ValueError):
                benchmark(path)

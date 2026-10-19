import unittest
from agentlab.runner import Scenario, benchmark, run


class ReliabilityTests(unittest.TestCase):
    def test_transient_recovery(self):
        s = Scenario('timeout', ('timeout',))
        self.assertFalse(run(s, 'baseline')['success'])
        recovered = run(s, 'retry_validate')
        self.assertTrue(recovered['success'])
        self.assertEqual(recovered['attempts'], 2)

    def test_persistent_failure_is_bounded(self):
        r = run(Scenario('down', ('timeout',) * 10), 'retry_validate')
        self.assertFalse(r['success'])
        self.assertEqual(r['attempts'], 3)

    def test_wrong_order_never_counts_as_success(self):
        for policy in ('baseline', 'retry_validate'):
            self.assertFalse(run(Scenario('wrong', ('wrong_order',) * 4), policy)['success'])

    def test_malformed_response_recovery(self):
        r = run(Scenario('bad', ('malformed',)), 'retry_validate')
        self.assertTrue(r['success'])
        self.assertEqual(r['trace'][0]['outcome'], 'invalid_response')

    def test_report_has_individual_evidence(self):
        report = benchmark()
        self.assertEqual(len(report['results']), 12)
        self.assertEqual(report['summary']['baseline']['passed'], 1)
        self.assertEqual(report['summary']['retry_validate']['passed'], 4)
        self.assertTrue(all(r['trace'] for r in report['results']))

    def test_unknown_policy_rejected(self):
        with self.assertRaises(ValueError):
            run(Scenario('ok', ()), 'unknown')


if __name__ == '__main__':
    unittest.main()

from copy import deepcopy
import unittest
from agentlab.dashboard import build_report
from agentlab.regression import check


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_report()

    def test_current_behavior_matches_versioned_baseline(self):
        check(self.report)

    def test_gate_rejects_success_regression_or_hidden_failure(self):
        for section, index in [('lookup', 0), ('lookup', 1), ('replay', 2)]:
            report = deepcopy(self.report)
            row = report[section]['results'][index]
            row['success'] = not row['success']
            with self.assertRaises(ValueError):
                check(report)

    def test_gate_rejects_extra_calls_duplicate_writes_and_lost_resume(self):
        for field in ('calls', 'writes', 'resume'):
            report = deepcopy(self.report)
            if field == 'calls':
                report['lookup']['results'][0]['attempts'] += 1
            elif field == 'writes':
                report['support']['results'][0]['final_state']['tickets'].append(('extra', 'ticket'))
            else:
                report['durable']['checkpoint']['status'] = 'pending'
            with self.assertRaises(ValueError):
                check(report)

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agentlab.runner import benchmark, run
from agentlab.scenarios import Scenario, load_suite, parse_suite


def document():
    return {'schema_version': 1, 'suite': 'test-suite', 'seed': 42,
            'scenarios': [{'name': 'healthy', 'faults': []}]}


class ScenarioTests(unittest.TestCase):
    def test_explicit_schedule_and_order_survive_loading(self):
        d = document()
        d['scenarios'][0].update(faults=['timeout', 'none'], expected_order='custom-order')
        suite = parse_suite(d)
        self.assertEqual(suite.scenarios[0], Scenario('healthy', ('timeout', 'none'), 'custom-order'))
        self.assertTrue(run(suite.scenarios[0], 'retry_validate')['success'])

    def test_wrong_order_fault_always_differs_from_expected(self):
        self.assertFalse(run(Scenario('collision', ('wrong_order',) * 3, 'order-other'), 'retry_validate')['success'])

    def test_unknown_fields_and_versions_rejected(self):
        for key, value in [('schema_version', 2), ('schema_version', True), ('seed', True), ('seed', -1), ('typo', 1)]:
            d = document()
            d[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                parse_suite(d)
        d = document()
        d['scenarios'][0]['fault'] = []
        with self.assertRaises(ValueError):
            parse_suite(d)

    def test_bad_scenarios_rejected(self):
        bad_rows = [[], [{'name': 'same', 'faults': []}] * 2,
                    [{'name': 'bad name', 'faults': []}],
                    [{'name': 'valid', 'faults': ['typo']}],
                    [{'name': 'valid', 'faults': [1]}],
                    [{'name': 'valid', 'faults': [], 'expected_order': ''}],
                    [{'name': 'valid'}],
                    [{'name': 'valid', 'faults': [], 'generator': {'pool': ['none'], 'attempts': 1}}]]
        for rows in bad_rows:
            d = document()
            d['scenarios'] = rows
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                parse_suite(d)

    def test_bad_generators_rejected(self):
        for generator in [{'pool': [], 'attempts': 3}, {'pool': ['timeout'], 'attempts': True},
                          {'pool': ['timeout'], 'attempts': 101}, {'pool': ['bad'], 'attempts': 1},
                          {'pool': ['none'], 'attempts': 1, 'unexpected': 1}]:
            d = document()
            d['scenarios'] = [{'name': 'generated', 'generator': generator}]
            with self.subTest(generator=generator), self.assertRaises(ValueError):
                parse_suite(d)

    def test_seed_is_stable_and_independent_of_order(self):
        d = document()
        row = {'name': 'generated', 'generator': {'pool': ['none', 'timeout', 'rate_limit'], 'attempts': 20}}
        d['scenarios'].append(row)
        a = parse_suite(d)
        self.assertEqual(a, parse_suite(copy.deepcopy(d)))
        d['scenarios'].reverse()
        b = parse_suite(d)
        self.assertEqual(a.scenarios[1], b.scenarios[0])
        self.assertNotEqual(a.scenarios[1].faults, parse_suite(d, seed=43).scenarios[0].faults)
        self.assertEqual(d['seed'], 42)  # Overrides must not mutate source documents.
        with self.assertRaises(ValueError):
            parse_suite(d, seed=True)

    def test_json_duplicate_keys_and_nonstandard_constants_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bad.json'
            for payload in ['{"schema_version":1,"schema_version":1}', '{"seed": NaN}', '{}', 'not json']:
                path.write_text(payload)
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    load_suite(path)

    def test_file_and_collection_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'large.json'
            path.write_bytes(b' ' * 1_048_577)
            with self.assertRaises(ValueError):
                load_suite(path)
        for changes in [{'scenarios': document()['scenarios'] * 1001},
                        {'scenarios': [{'name': 'long', 'faults': ['none'] * 101}]}]:
            d = document()
            d.update(changes)
            with self.assertRaises(ValueError):
                parse_suite(d)

    def test_report_contains_source_fingerprint_and_expanded_schedule(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'suite.json'
            path.write_text(json.dumps(document()))
            r = benchmark(path, seed=7)
            self.assertEqual(r['seed'], 7)
            self.assertEqual(r['suite'], 'test-suite')
            self.assertEqual(len(r['source_sha256']), 64)
            self.assertEqual(r['scenarios'][0]['faults'], ())
            self.assertEqual(r['summary']['baseline']['total'], 1)

    def test_cli_rejects_bad_input_without_creating_report(self):
        with tempfile.TemporaryDirectory() as temp:
            suite = Path(temp) / 'bad.json'
            output = Path(temp) / 'report.json'
            suite.write_text('{"schema_version":99}')
            r = subprocess.run([sys.executable, '-m', 'agentlab.runner', '--scenarios', str(suite),
                                '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn('error:', r.stderr)
            self.assertNotIn('Traceback', r.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()

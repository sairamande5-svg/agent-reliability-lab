import tempfile
from pathlib import Path
import unittest
from agentlab.dashboard import publish
from agentlab.history import RunStore, validate_id


class HistoryTests(unittest.TestCase):
    def test_history_survives_reopen_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'runs.sqlite'
            store = RunStore(path)
            store.save('first', {'value': 1})
            store.close()
            store = RunStore(path)
            try:
                store.save('second', {'value': 2})
                self.assertEqual(list(store.recent()), ['second', 'first'])
                with self.assertRaises(ValueError):
                    store.save('first', {'value': 99})
                self.assertEqual(store.recent()['first'], {'value': 1})
                with self.assertRaises(ValueError):
                    store.save('huge', {'value': 'x' * 1_048_576})
            finally:
                store.close()

    def test_identifiers_reject_traversal_queries_and_sql(self):
        for value in ('../secret', 'x/y', 'a?file=x', "a' OR 1=1", '', 'x'*65, None):
            with self.assertRaises(ValueError):
                validate_id(value)

    def test_exports_include_independent_saved_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            publish(output, 'before')
            report = publish(output, 'after')
            self.assertEqual(list(report['history']), ['after', 'before'])
            self.assertNotIn('history', report['history']['before'])
            self.assertTrue(report['history']['before']['durable']['final_state']['success'])
            with self.assertRaises(ValueError):
                publish(output, 'before')

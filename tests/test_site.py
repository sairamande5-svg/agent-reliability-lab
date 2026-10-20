import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.build_site import build


class StaticSiteTests(unittest.TestCase):
    def test_public_export_contains_only_static_evidence_and_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = build(output, 'a' * 40)
            self.assertEqual({p.name for p in output.iterdir()},
                             {'index.html', 'report.json', '.nojekyll', 'SHA256SUMS'})
            self.assertEqual(report['build']['source_commit'], 'a' * 40)
            self.assertEqual(len(report['history']), 2)
            self.assertEqual(report['process_crash']['summary'], {'passed': 4, 'total': 4})
            self.assertEqual(json.loads((output / 'report.json').read_text())['build'], report['build'])
            self.assertNotIn('__REPORT_JSON__', (output / 'index.html').read_text())
            for line in (output / 'SHA256SUMS').read_text().splitlines():
                digest, name = line.split('  ')
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)

    def test_existing_private_files_are_not_published_or_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            private = output / 'runs.sqlite'
            private.write_bytes(b'preserve-existing-data')
            with self.assertRaises(ValueError):
                build(output)
            self.assertEqual(private.read_bytes(), b'preserve-existing-data')
            self.assertFalse((output / 'index.html').exists())

    def test_invalid_source_commit_does_not_write_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'site'
            with self.assertRaises(ValueError):
                build(output, '../invalid')
            self.assertFalse(output.exists())

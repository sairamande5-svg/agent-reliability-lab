from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from agentlab.dashboard import Handler, publish, render


class DashboardTests(unittest.TestCase):
    def test_export_contains_real_results_and_resumed_database_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = publish(output)
            self.assertEqual(json.loads((output / 'report.json').read_text()), json.loads(json.dumps(report)))
            html = (output / 'index.html').read_text()
            self.assertNotIn('__REPORT_JSON__', html)
            self.assertEqual(report['lookup']['summary']['retry_validate']['passed'], 4)
            self.assertEqual(report['durable']['checkpoint']['status'], 'completed')
            self.assertEqual(report['durable']['checkpoint']['attempts'], 2)
            self.assertTrue(report['durable']['final_state']['success'])
            self.assertEqual(report['durable']['final_state']['action_count'], 1)

    def test_untrusted_embedded_json_cannot_close_script(self):
        payload = '</script><script>alert("unsafe")</script>&'
        html = render({'trace': payload})
        self.assertNotIn(payload, html)
        embedded = html.split('<script id="report" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(embedded), {'trace': payload})
        self.assertNotIn('innerHTML', html)

    def test_fixed_read_only_api_rejects_unknown_and_traversal_paths(self):
        report = {'kind': 'test'}
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, report=report))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base + '/api/report') as response:
                self.assertEqual(json.load(response), report)
                self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
            for path in ('/../README.md', '/%2e%2e/README.md', '/api/report?file=README.md', '/unknown'):
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + path)
                self.assertEqual(error.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

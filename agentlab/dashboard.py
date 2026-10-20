"""Generate a portable, offline dashboard from freshly executed experiments."""
import argparse
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .durable import DurableRun
from .runner import benchmark as lookup_benchmark
from .stateful import InjectedCrash, SupportTools, verify_outcome
from .stateful_runner import benchmark as support_benchmark

TEMPLATE = Path(__file__).with_name('dashboard.html')


def durable_demo():
    with TemporaryDirectory() as directory:
        database = Path(directory) / 'durable.sqlite'
        tools = SupportTools(database)
        tools.seed_order()
        tools.close()
        run = DurableRun(database, clock=lambda: 0)
        run.create('demo-recovery')
        try:
            run.step('demo-recovery', fault='before_ack')
        except InjectedCrash:
            pass
        finally:
            run.close()
        # Construct a new executor from persisted identity, not a saved Python object.
        resumed = DurableRun(database, clock=lambda: 1)
        try:
            checkpoint = resumed.step('demo-recovery')
        finally:
            resumed.close()
        return {'checkpoint': checkpoint, 'final_state': verify_outcome(database)}


def build_report():
    return {'schema_version': 1, 'kind': 'scripted-offline-demo',
            'lookup': lookup_benchmark(), 'support': support_benchmark(),
            'durable': durable_demo()}


def render(report):
    # JSON embedded in an HTML script element must not permit closing that element.
    payload = json.dumps(report, allow_nan=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return TEMPLATE.read_text().replace('__REPORT_JSON__', payload)


def publish(output: Path):
    report = build_report()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'index.html').write_text(render(report))
    return report


class Handler(BaseHTTPRequestHandler):
    """Fixed routes only. Never map user-controlled paths to the filesystem."""
    def __init__(self, *args, report, **kwargs):
        self.report = report
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            body, content_type = render(self.report).encode(), 'text/html; charset=utf-8'
        elif self.path == '/api/report':
            body, content_type = json.dumps(self.report).encode(), 'application/json'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/demo'))
    parser.add_argument('--serve', action='store_true', help='serve generated evidence and fixed read-only API')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('port must be between 0 and 65535')
    report = publish(args.output)
    print(f'Generated {args.output / "index.html"} and report.json', flush=True)
    if args.serve:
        with ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, report=report)) as server:
            print(f'Serving offline dashboard on port {server.server_port}; Ctrl-C to stop.', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == '__main__':
    main()

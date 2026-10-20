"""Kill real workers at synchronized write boundaries, then resume in a new process."""
import argparse
import json
from pathlib import Path
from queue import Empty, Queue
import signal
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread

from .crash_worker import BOUNDARIES
from .durable import DurableRun
from .stateful import SupportTools, verify_outcome


def experiment(boundary):
    if boundary not in BOUNDARIES:
        raise ValueError('unknown process crash boundary')
    with TemporaryDirectory() as directory:
        database = Path(directory) / 'process.sqlite'
        tools = SupportTools(database)
        tools.seed_order()
        tools.close()
        run = DurableRun(database, clock=lambda: 0)
        try:
            action_id = run.create('process-recovery')['action_id']
        finally:
            run.close()
        command = [sys.executable, '-m', 'agentlab.crash_worker', '--database', str(database)]
        worker = subprocess.Popen(command + ['--boundary', boundary, '--now', '0'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
        messages = Queue()
        reader = Thread(target=lambda: messages.put(worker.stdout.readline()), daemon=True)
        reader.start()
        try:
            try:
                message = json.loads(messages.get(timeout=10))
            except (Empty, ValueError) as exc:
                raise RuntimeError('worker did not reach the crash boundary') from exc
            if message != {'boundary': boundary}:
                raise RuntimeError('worker reported an unexpected boundary')
            worker.kill()
            worker.wait(timeout=10)
            if sys.platform != 'win32' and worker.returncode != -signal.SIGKILL:
                raise RuntimeError('worker was not terminated by SIGKILL')
        finally:
            if worker.poll() is None:
                worker.kill()
            worker.communicate(timeout=10)
            reader.join(timeout=10)
        before = verify_outcome(database)
        checkpoint = DurableRun(database)
        try:
            interrupted = checkpoint.state('process-recovery')
        finally:
            checkpoint.close()
        resumed = subprocess.run(command + ['--now', '1'], capture_output=True,
                                 text=True, timeout=10, check=True)
        completed = json.loads(resumed.stdout)
        final = verify_outcome(database)
        with sqlite3.connect(database) as connection:
            integrity = connection.execute('PRAGMA integrity_check').fetchone()[0]
            journal = connection.execute('PRAGMA journal_mode').fetchone()[0]
        identity_preserved = completed['action_id'] == action_id
        success = (final['success'] and final['action_count'] == 1
                   and completed['status'] == 'completed' and completed['attempts'] == 2
                   and identity_preserved and integrity == 'ok'
                   and interrupted['status'] == 'pending'
                   and interrupted['trace'][0]['outcome'] == 'started'
                   and before['success'] == (boundary in ('before_ack', 'after_ack')))
        return {'scenario': boundary, 'kind': 'real-process-kill', 'success': success,
                'exit_code': worker.returncode, 'kill_method': 'SIGKILL' if sys.platform != 'win32' else 'TerminateProcess',
                'journal_mode': journal, 'integrity_check': integrity,
                'identity_preserved': identity_preserved, 'before_resume': before,
                'checkpoint': completed, 'final_state': final,
                'trace': [{'outcome': 'worker_killed', 'point': boundary},
                          {'outcome': 'resumed_in_new_process'}]}


def benchmark():
    results = [experiment(boundary) for boundary in BOUNDARIES]
    return {'schema_version': 1, 'kind': 'real-process-kill',
            'limitations': 'Synchronized local worker termination, not host power loss, distributed execution, or production evidence.',
            'results': results, 'summary': {'passed': sum(row['success'] for row in results),
                                          'total': len(results)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/process-crash.json'))
    args = parser.parse_args()
    report = benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary']))
    if not all(row['success'] for row in report['results']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()

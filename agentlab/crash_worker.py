"""Internal worker for deterministic process-kill experiments; no external services."""
import argparse
import json
import sys

from .durable import DurableRun

BOUNDARIES = ('before_write', 'during_write', 'before_ack', 'after_ack')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--boundary', choices=BOUNDARIES)
    parser.add_argument('--now', type=float, required=True)
    args = parser.parse_args()

    def pause(point):
        if point == args.boundary:
            # Handshake occurs while the worker is AT the boundary, never after it.
            print(json.dumps({'boundary': point}), flush=True)
            # Parent kills this process. Do not release the boundary or close SQLite.
            sys.stdin.buffer.read(1)
            raise RuntimeError('worker released without a process kill')

    run = DurableRun(args.database, clock=lambda: args.now)
    try:
        result = run.step('process-recovery', on_boundary=pause)
        print(json.dumps(result), flush=True)
    finally:
        run.close()


if __name__ == '__main__':
    main()

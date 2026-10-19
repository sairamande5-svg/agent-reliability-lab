"""Bounded, scripted support-write experiment on isolated temporary databases."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .stateful import InjectedCrash, SupportTools, verify_outcome


def benchmark():
    results = []
    with TemporaryDirectory() as directory:
        for fault in ('none', 'before_write', 'before_ack', 'after_ack'):
            database = Path(directory) / (fault + '.sqlite')
            trace = []
            for attempt in range(2):
                tools = SupportTools(database)
                try:
                    tools.seed_order()
                    response = tools.open_ticket('support-action-001', 'order-001',
                                                 'missing parcel', fault=fault if attempt == 0 else 'none')
                    trace.append({'attempt': attempt + 1, 'outcome': 'acknowledged',
                                  'response': response})
                    break
                except InjectedCrash as exc:
                    trace.append({'attempt': attempt + 1, 'outcome': 'crash',
                                  'point': str(exc), 'acknowledgment': exc.acknowledgment})
                finally:
                    tools.close()
            results.append({'scenario': fault, 'trace': trace,
                            'final_state': verify_outcome(database)})
    return {'schema_version': 1, 'suite': 'synthetic-support-v1',
            'limitations': 'Scripted offline fixtures. Crashes are exceptions at defined boundaries, '
                            'not OS failures. Action identity is held in memory; no durable policy resume.',
            'results': results,
            'summary': {'passed': sum(row['final_state']['success'] for row in results),
                        'total': len(results)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/stateful.json'))
    args = parser.parse_args()
    report = benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary']))


if __name__ == '__main__':
    main()

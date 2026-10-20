"""One-command local release verification: tests, fresh evidence, regression gate."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from .dashboard import publish
from .regression import check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--properties', action='store_true', help='also run optional Hypothesis invariant tests')
    parser.add_argument('--output', type=Path, default=Path('artifacts/portfolio'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=root, check=True)
    if args.properties:
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'property_tests', '-v'], cwd=root, check=True)
    try:
        report = publish(args.output)
        check(report)
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps({'regression': 'passed', 'report': str(args.output / 'report.json'),
                      'dashboard': str(args.output / 'index.html'),
                      'lookup': report['lookup']['summary'], 'support': report['support']['summary'],
                      'replay': report['replay']['summary'],
                      'process_crash': report['process_crash']['summary']}, indent=2))


if __name__ == '__main__':
    main()

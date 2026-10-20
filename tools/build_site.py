"""Build only public synthetic evidence; never publish the SQLite history database."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from agentlab.dashboard import publish, render
from agentlab.regression import check


def build(output: Path, source_commit=None):
    if source_commit is not None and not re.fullmatch(r'[0-9a-f]{40}', source_commit):
        raise ValueError('source commit must be a full lowercase Git SHA')
    public_files = {'index.html', 'report.json', '.nojekyll', 'SHA256SUMS'}
    if output.exists():
        if not output.is_dir() or any(p.name not in public_files or p.is_symlink() or not p.is_file()
                                      for p in output.iterdir()):
            raise ValueError('site output must be empty or contain only previously generated public files')
    with TemporaryDirectory() as directory:
        # Two fresh executions of the same fixed fixtures, not two different model versions.
        publish(Path(directory), 'sample-a')
        report = publish(Path(directory), 'sample-b')
        check(report)
    report['build'] = {'source_commit': source_commit, 'type': 'static-synthetic-demo',
                       'comparison': 'Two fresh executions of the same fixed suites; not model performance comparisons.'}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'index.html').write_text(render(report))
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / '.nojekyll').touch()
    checksums = [f'{hashlib.sha256((output / name).read_bytes()).hexdigest()}  {name}'
                 for name in ('index.html', 'report.json')]
    (output / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/site'))
    parser.add_argument('--source-commit')
    args = parser.parse_args()
    try:
        build(args.output, args.source_commit)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f'Static demo and evidence built in {args.output}')


if __name__ == '__main__':
    main()

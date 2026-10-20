"""Exact offline behavioral regression gate; timing and random IDs are excluded."""
import json
from pathlib import Path

BASELINE = Path(__file__).resolve().parent.parent / 'baselines' / 'offline-v2.json'


def signature(report):
    def rows(items, key, fields):
        result = {}
        for row in items:
            name = key(row)
            if name in result:
                raise ValueError('duplicate result identity')
            result[name] = {field: row[field] for field in fields}
        return result
    return {
        'schema_version': 2,
        'process_crash': {r['scenario']: {field: r[field] for field in
            ('success', 'journal_mode', 'integrity_check', 'identity_preserved', 'before_resume', 'final_state')}
            for r in report['process_crash']['results']},
        'lookup_source': report['lookup']['source_sha256'],
        'lookup': rows(report['lookup']['results'], lambda r: r['policy'] + '/' + r['scenario'], ('success', 'attempts')),
        'support': {r['scenario']: r['final_state'] for r in report['support']['results']},
        'replay_source': report['replay']['source_sha256'],
        'replay': rows(report['replay']['results'], lambda r: r['scenario'], ('success', 'tool_calls', 'budget_exhausted')),
        'durable': {'status': report['durable']['checkpoint']['status'],
                    'attempts': report['durable']['checkpoint']['attempts'],
                    'final_state': report['durable']['final_state']},
    }


def check(report, baseline=BASELINE):
    expected = json.loads(Path(baseline).read_text())
    # Normalize tuples from direct Python reports to their exported JSON representation.
    actual = json.loads(json.dumps(signature(report), allow_nan=False))
    if actual != expected:
        changed = [key for key in expected.keys() | actual.keys() if expected.get(key) != actual.get(key)]
        raise ValueError('offline regression mismatch: ' + ', '.join(sorted(changed)))
    return actual

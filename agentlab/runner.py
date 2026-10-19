"""Controlled retry experiment for a simulated order lookup tool."""
import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from time import perf_counter


@dataclass(frozen=True)
class Scenario:
    name: str
    faults: tuple[str, ...]
    expected_order: str = 'order-001'


SCENARIOS = (
    Scenario('healthy', ()),
    Scenario('transient_timeout', ('timeout',)),
    Scenario('rate_limit_then_success', ('rate_limit',)),
    Scenario('malformed_then_success', ('malformed',)),
    Scenario('persistent_timeout', ('timeout',) * 4),
    Scenario('wrong_order', ('wrong_order',) * 4),
)


class TransientToolError(Exception):
    pass


def run(scenario: Scenario, policy: str) -> dict:
    if policy not in ('baseline', 'retry_validate'):
        raise ValueError('unknown policy')
    budget = 1 if policy == 'baseline' else 3
    trace = []
    started = perf_counter()
    success = False
    for attempt in range(budget):
        fault = scenario.faults[attempt] if attempt < len(scenario.faults) else 'none'
        try:
            if fault in ('timeout', 'rate_limit'):
                raise TransientToolError(fault)
            response = ({'unexpected': True} if fault == 'malformed' else {
                'order_id': 'order-other' if fault == 'wrong_order' else scenario.expected_order,
                'status': 'shipped',
            })
            valid = (response.get('order_id') == scenario.expected_order
                     and response.get('status') == 'shipped')
            # The independent outcome check applies to both policies.
            success = valid
            trace.append({'attempt': attempt + 1, 'fault': fault,
                          'response': response, 'outcome': 'success' if valid else 'invalid_response'})
            if valid or policy == 'baseline':
                break
        except TransientToolError as exc:
            trace.append({'attempt': attempt + 1, 'fault': fault, 'outcome': str(exc)})
    return {'scenario': scenario.name, 'policy': policy, 'success': success,
            'attempts': len(trace), 'elapsed_ms': (perf_counter() - started) * 1000,
            'trace': trace}


def benchmark() -> dict:
    results = [run(s, policy) for policy in ('baseline', 'retry_validate') for s in SCENARIOS]
    summary = {}
    for policy in ('baseline', 'retry_validate'):
        rows = [r for r in results if r['policy'] == policy]
        summary[policy] = {'passed': sum(r['success'] for r in rows), 'total': len(rows),
                           'tool_calls': sum(r['attempts'] for r in rows)}
    return {'schema_version': 1, 'suite': 'lookup-fixtures-v1',
            'limitations': 'Scripted fixtures, not live LLMs. Timings measure local Python only. No model cost measured.',
            'scenarios': [asdict(s) for s in SCENARIOS], 'summary': summary, 'results': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/benchmark.json'))
    args = parser.parse_args()
    report = benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()

"""Provider-neutral decisions and bounded offline transcript evaluation. No model calls."""
import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from .scenarios import _integer, _object, _unique_object, _invalid_constant, _identifier
from .stateful import FAULTS, InjectedCrash, SupportTools, verify_outcome

DEFAULT_SUITE = Path(__file__).resolve().parent.parent / 'scenarios' / 'replay-heldout-v1.json'


@dataclass(frozen=True)
class Decision:
    tool: str
    arguments: dict


class Adapter(Protocol):
    def decide(self, task: dict, observations: tuple[dict, ...]) -> Decision:
        """Return a tool decision or finish. Implementations must enforce their own I/O timeout."""
        ...


class ReplayAdapter:
    """Replay authored decisions; this is not a recording of a live model."""
    def __init__(self, decisions):
        self.decisions = iter(decisions)

    def decide(self, task, observations):
        return next(self.decisions, Decision('finish', {}))


def evaluate(adapter: Adapter, task: dict, *, faults=(), budget=4):
    _integer(budget, 1, 20, 'budget')
    for key in ('order_id', 'reason'):
        SupportTools._text(task[key])
    if any(fault not in FAULTS for fault in faults) or len(faults) > 20:
        raise ValueError('invalid fault schedule')
    trace = []
    tool_calls = 0
    with TemporaryDirectory() as directory:
        database = Path(directory) / 'support.sqlite'
        tools = SupportTools(database)
        tools.seed_order(task['order_id'])
        try:
            for step in range(budget):
                try:
                    # Give adapters detached context so they cannot mutate grader expectations.
                    decision = adapter.decide(dict(task), tuple(json.loads(json.dumps(trace))))
                    if not isinstance(decision, Decision):
                        raise ValueError('adapter must return Decision')
                    args = decision.arguments
                    if decision.tool == 'finish':
                        _object(args, set(), set(), 'finish')
                        trace.append({'step': step + 1, 'tool': 'finish', 'outcome': 'finished'})
                        break
                    if decision.tool == 'lookup_order':
                        _object(args, {'order_id'}, set(), 'lookup_order')
                        tool_calls += 1
                        response = tools.lookup_order(args['order_id'])
                    elif decision.tool == 'open_ticket':
                        _object(args, {'action_id', 'order_id', 'reason'}, set(), 'open_ticket')
                        fault = faults[tool_calls] if tool_calls < len(faults) else 'none'
                        tool_calls += 1
                        response = tools.open_ticket(**args, fault=fault)
                    else:
                        raise ValueError('unsupported tool')
                    trace.append({'step': step + 1, 'tool': decision.tool,
                                  'outcome': 'acknowledged', 'response': response})
                except InjectedCrash as exc:
                    trace.append({'step': step + 1, 'outcome': 'crash', 'point': str(exc)})
                except (ValueError, TypeError, KeyError) as exc:
                    trace.append({'step': step + 1, 'outcome': 'invalid_decision', 'error': str(exc)})
            final_state = verify_outcome(database, task['order_id'], task['reason'])
        finally:
            tools.close()
    return {'kind': 'offline-replay', 'budget': budget, 'decisions': len(trace),
            'tool_calls': tool_calls, 'budget_exhausted': len(trace) == budget and trace[-1]['outcome'] != 'finished',
            'trace': trace, 'final_state': final_state, 'success': final_state['success'],
            'tokens': None, 'cost_usd': None}


def benchmark(path=DEFAULT_SUITE):
    with Path(path).open('rb') as stream:
        raw = stream.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ValueError('replay suite exceeds 1 MiB')
    doc = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    _object(doc, {'schema_version', 'split', 'cases'}, set(), 'suite')
    if type(doc['schema_version']) is not int or doc['schema_version'] != 1 or doc['split'] != 'heldout':
        raise ValueError('expected heldout replay suite version 1')
    if not isinstance(doc['cases'], list) or not 1 <= len(doc['cases']) <= 100:
        raise ValueError('expected 1–100 cases')
    names, results = set(), []
    for case in doc['cases']:
        _object(case, {'name', 'task', 'decisions', 'faults', 'budget'}, set(), 'case')
        name = _identifier(case['name'], 'case name')
        if name in names:
            raise ValueError('duplicate case name')
        names.add(name)
        _object(case['task'], {'order_id', 'reason'}, set(), 'task')
        if not isinstance(case['decisions'], list) or len(case['decisions']) > 20:
            raise ValueError('expected at most 20 decisions')
        decisions = []
        for row in case['decisions']:
            _object(row, {'tool', 'arguments'}, set(), 'decision')
            if not isinstance(row['tool'], str) or not isinstance(row['arguments'], dict):
                raise ValueError('invalid decision types')
            decisions.append(Decision(**row))
        if not isinstance(case['faults'], list) or any(not isinstance(f, str) for f in case['faults']):
            raise ValueError('faults must be a list of strings')
        results.append({'scenario': name, **evaluate(ReplayAdapter(decisions), case['task'],
                                                   faults=case['faults'], budget=case['budget'])})
    return {'schema_version': 1, 'kind': 'offline-replay', 'split': 'heldout',
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'limitations': 'Authored synthetic transcripts, not live model recordings. Held apart from lookup fixtures; not a statistical held-out model evaluation.',
            'results': results, 'summary': {'passed': sum(r['success'] for r in results), 'total': len(results)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, default=DEFAULT_SUITE)
    parser.add_argument('--output', type=Path, default=Path('artifacts/replay.json'))
    args = parser.parse_args()
    try:
        report = benchmark(args.suite)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary']))


if __name__ == '__main__':
    main()

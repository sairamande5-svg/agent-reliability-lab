"""Strict v1 scenario documents and stable, seeded fault expansion."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

FAULTS = frozenset({'none', 'timeout', 'rate_limit', 'malformed', 'wrong_order'})
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}')


@dataclass(frozen=True)
class Scenario:
    name: str
    faults: tuple[str, ...]
    expected_order: str = 'order-001'


@dataclass(frozen=True)
class Suite:
    name: str
    seed: int
    scenarios: tuple[Scenario, ...]
    source_sha256: str


def _object(value, required, optional, label):
    if not isinstance(value, dict):
        raise ValueError(f'{label}: expected object')
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing or unknown:
        raise ValueError(f'{label}: missing {sorted(missing)}, unknown {sorted(unknown)}')


def _integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{label}: expected integer in [{low}, {high}]')
    return value


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f'{label}: expected 1–80 letters, digits, dots, underscores or hyphens')
    return value


def _faults(value, label):
    if not isinstance(value, list) or len(value) > 100:
        raise ValueError(f'{label}: expected list of at most 100 faults')
    if any(not isinstance(f, str) or f not in FAULTS for f in value):
        raise ValueError(f'{label}: unrecognized fault')
    return tuple(value)


def parse_suite(document, *, seed=None, source_sha256=''):
    _object(document, {'schema_version', 'suite', 'scenarios'}, {'seed'}, 'suite')
    if type(document['schema_version']) is not int or document['schema_version'] != 1:
        raise ValueError('unsupported schema_version; expected integer 1')
    name = _identifier(document['suite'], 'suite name')
    configured_seed = _integer(document.get('seed', 0), 0, 2**63 - 1, 'seed')
    effective_seed = configured_seed if seed is None else _integer(seed, 0, 2**63 - 1, 'seed override')
    rows = document['scenarios']
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError('scenarios: expected 1–1000 scenarios')
    scenarios, names = [], set()
    for i, row in enumerate(rows):
        label = f'scenarios[{i}]'
        _object(row, {'name'}, {'faults', 'generator', 'expected_order'}, label)
        scenario_name = _identifier(row['name'], label + '.name')
        if scenario_name in names:
            raise ValueError(f'duplicate scenario name: {scenario_name}')
        names.add(scenario_name)
        order = row.get('expected_order', 'order-001')
        if not isinstance(order, str) or not order.strip() or len(order) > 200:
            raise ValueError(label + '.expected_order: expected nonblank string of at most 200 characters')
        if ('faults' in row) == ('generator' in row):
            raise ValueError(label + ': provide exactly one of faults or generator')
        if 'faults' in row:
            faults = _faults(row['faults'], label + '.faults')
        else:
            generator = row['generator']
            _object(generator, {'pool', 'attempts'}, set(), label + '.generator')
            pool = _faults(generator['pool'], label + '.generator.pool')
            if not pool:
                raise ValueError(label + '.generator.pool: must not be empty')
            count = _integer(generator['attempts'], 1, 100, label + '.generator.attempts')
            # sha256-v1: independent of document ordering and Python PRNG versions.
            faults = tuple(pool[int.from_bytes(hashlib.sha256(
                f'{effective_seed}:{scenario_name}:{attempt}'.encode('utf-8')).digest(), 'big') % len(pool)]
                for attempt in range(count))
        scenarios.append(Scenario(scenario_name, faults, order))
    return Suite(name, effective_seed, tuple(scenarios), source_sha256)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f'nonstandard JSON constant: {value}')


def load_suite(path: Path, *, seed=None):
    # Bound input size before reading; scenario and attempt counts are bounded too.
    with Path(path).open('rb') as stream:
        raw = stream.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ValueError('scenario file exceeds 1 MiB')
    document = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                          parse_constant=_invalid_constant)
    return parse_suite(document, seed=seed, source_sha256=hashlib.sha256(raw).hexdigest())

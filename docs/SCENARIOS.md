# Scenario document v1

Run an explicit suite:
```sh
python -m agentlab.runner --scenarios scenarios/lookup-v1.json
python -m agentlab.runner --scenarios scenarios/seeded-v1.json --seed 7 --output artifacts/seeded.json
```

The loader accepts UTF-8 JSON, at most 1 MiB. Required top-level fields are integer `schema_version: 1`, `suite`, and `scenarios`; optional `seed` defaults to 0. Unknown fields, duplicate JSON keys, nonstandard constants such as NaN, and unsupported versions are errors. Errors exit the CLI with code 2 before a report is written.

Suite and scenario names contain 1–80 ASCII letters, digits, dots, underscores, or hyphens, starting with a letter or digit. A suite holds 1–1000 uniquely named scenarios. `expected_order` optionally overrides `order-001` with a nonblank string up to 200 characters.

Each scenario specifies exactly one of:

- `faults`: a list of 0–100 strings from `none`, `timeout`, `rate_limit`, `malformed`, `wrong_order`.
- `generator`: an object with `pool` (1–100 allowed fault strings) and `attempts` (integer 1–100).

Example:
```json
{
  "schema_version": 1,
  "suite": "example-v1",
  "seed": 42,
  "scenarios": [
    {"name": "transient", "faults": ["timeout", "none"]},
    {"name": "mixed", "generator": {"pool": ["none", "timeout"], "attempts": 3}}
  ]
}
```

Seeds are integers from 0 to 2^63−1. `--seed` overrides the document seed without modifying the source. For generator `sha256-v1`, attempt index starts at zero. Encode `<seed>:<scenario_name>:<index>` as UTF-8, hash with SHA-256, interpret the digest as an unsigned big-endian integer, and choose `pool[integer % len(pool)]`. Expansion does not depend on scenario order or the Python random implementation. Duplicate pool entries intentionally weight a fault. This is deterministic fault selection, not a statistically validated sampling method.

Schedules describe outcomes per tool attempt; attempts after the explicit/generated schedule receive a healthy response. Baseline makes one attempt; retry/validate makes at most three. A long fault schedule does not increase that execution budget.

Reports include the effective seed, generator identifier, SHA-256 of the exact source bytes, and expanded scenario schedules. Whitespace changes alter the source fingerprint. Wall-clock elapsed times vary between executions even when schedules and outcomes match. Neither these timings nor pass rates measure live model quality or API latency.

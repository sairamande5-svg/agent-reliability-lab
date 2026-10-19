# Agent Reliability Lab

An evaluation workbench for tool-using agents under controlled failures.

## Current status
Milestone 1 complete: a dependency-free deterministic tool simulator and bounded retry experiment with strict versioned JSON scenario loading and reproducible seeded schedules. This is NOT yet a live AI agent benchmark. The two policies are scripted. No model calls, cloud services, credentials, or paid dependencies are needed.

## Run (Python 3.11+)
```sh
python -m unittest discover -s tests -v
python -m agentlab.runner --output artifacts/benchmark.json
```

Six versioned fixtures cover healthy responses, timeouts, rate limits, malformed responses, persistent failures, and wrong-order responses. Each report contains per-attempt evidence and an independent outcome check. The fixture construction intentionally favors recovery from transient failures; aggregate fixture pass rates do not establish general model quality. Local timings do not represent API latency.

Customize the fixtures with `--scenarios PATH` and override seeded fault generation with `--seed INTEGER`. Reports include expanded faults and a source fingerprint. See [scenario format](docs/SCENARIOS.md) for validation rules and examples.

## Planned architecture
Versioned scenarios → isolated mock tools → policy/model adapter → independent outcome checks → JSON traces → comparison API/dashboard.

See docs/ROADMAP.md for bounded implementation milestones and AGENTS.md for build and commit rules.


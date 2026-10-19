# Agent Reliability Lab

An evaluation workbench for tool-using agents under controlled failures.

## Current status
Milestones 1 and 2 complete: a dependency-free deterministic tool simulator and bounded retry experiment with strict versioned JSON scenario loading and reproducible seeded schedules. This is NOT yet a live AI agent benchmark. The two policies are scripted. No model calls, cloud services, credentials, or paid dependencies are needed.

## Run (Python 3.11+)
```sh
python -m unittest discover -s tests -v
python -m agentlab.runner --output artifacts/benchmark.json
python -m agentlab.stateful_runner --output artifacts/stateful.json
```

Six versioned fixtures cover healthy responses, timeouts, rate limits, malformed responses, persistent failures, and wrong-order responses. Each report contains per-attempt evidence and an independent outcome check. The fixture construction intentionally favors recovery from transient failures; aggregate fixture pass rates do not establish general model quality. Local timings do not represent API latency.

Customize the fixtures with `--scenarios PATH` and override seeded fault generation with `--seed INTEGER`. Reports include expanded faults and a source fingerprint. See [scenario format](docs/SCENARIOS.md) for validation rules and examples.

## Planned architecture
Versioned scenarios → isolated mock tools → policy/model adapter → independent outcome checks → JSON traces → comparison API/dashboard.

See docs/ROADMAP.md for bounded implementation milestones and AGENTS.md for build and commit rules.


## Stateful synthetic support tools
`agentlab.stateful.SupportTools` uses a local SQLite database with synthetic orders,
support tickets, action identities, and duplicate-event evidence. Seed an order with
`seed_order`, read it with `lookup_order`, and call
`open_ticket(action_id, order_id, reason)`. Keep the action ID stable across retries.
A repeated ID replays the same ticket; reusing an ID for a different payload fails.
A new ID for the same order/reason records a duplicate intent without another ticket.
This deliberately bounded model allows one ticket per order; a different reason conflicts.
Ticket creation and action recording commit together under a SQLite write transaction.

The stateful experiment runs healthy, before-write, before-acknowledgment, and
after-acknowledgment fixtures with at most two attempts each. `before_ack` commits
but hides the response; `after_ack` exposes the acknowledgment on the simulated
crash exception. Retrying is safe in both cases. The independent verifier opens a
separate read-only database connection and checks actual order/ticket contents,
including extra or incorrect records, rather than trusting returned text.
Databases are temporary; the JSON report retains final-state evidence and traces.
These are scripted boundary exceptions, not process kills or production evidence.
Durable policy checkpoints and automatic process restart remain milestone 3.

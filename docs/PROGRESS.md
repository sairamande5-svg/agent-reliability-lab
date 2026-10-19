# Progress

## Implemented
- Milestone 1: six controlled fixtures, bounded baseline/retry policies, per-attempt JSON traces, independent outcome validation, and strict versioned/seeded scenario loading.
- Milestone 2: dependency-free SQLite synthetic orders and support tickets, atomic ticket/action writes, payload-bound idempotency keys, replay detection, and duplicate-intent detection across different keys.
- Explicit simulated crashes before writing, after commit before acknowledgment, and after acknowledgment. Reopening the database and retrying preserves one ticket and one stable action identity.
- Independent read-only final-state checks reject incorrect or extra order/ticket state. A bounded offline stateful runner records traces and final-state evidence.

## Validation executed
- `python -m unittest discover -s tests -v`: all 23 tests passed locally.
- `python -m agentlab.runner --output /tmp/reliability-lookup.json`: scripted baseline 1/6 and retry/validate 4/6.
- `python -m agentlab.stateful_runner --output /tmp/reliability-stateful.json`: 4/4 scripted fixtures passed independent final-database checks.
- `python -m agentlab.runner --scenarios scenarios/seeded-v1.json --seed 7 --output /tmp/reliability-seeded.json`: scripted baseline 0/2 and retry/validate 1/2.
- `git diff --check`: passed.
- New tests exercise write replay, conflicting identities/payloads, duplicate intent, invalid inputs, all three crash boundaries, tool reopening, deliberately corrupted final state, and the stateful experiment.

## Limitations
No remote CI or live model evaluation has run. Policies and data are synthetic scripted fixtures, not production or model-quality evidence. Crashes are injected Python exceptions at defined boundaries, not OS/process kills or power failures. SQLite business state persists but policy action identity remains in memory; no durable checkpoints or automatic restart/resume yet. The support model permits one ticket per order; different reasons conflict. Duplicate telemetry records retries, not external real-world actions. The stateful runner uses temporary databases and retains their inspected state in JSON. Existing lookup scenario JSON remains separate from the fixed stateful fixtures.

## Next
Milestone 3: SQLite policy checkpoints and restart/resume with stable action identity, bounded backoff, and fake-clock tests. Verify resumed execution never duplicates business writes.

Milestone 2 is developed on `codex/reliability-milestone-2`, based on the unmerged `codex/reliability-foundation` branch. Default-branch merges await user authorization. Offline work needs no API keys and uses no paid APIs.

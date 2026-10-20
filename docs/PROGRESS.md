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

## Durable execution increment
- Added SQLite policy intent/action identity, attempt-start checkpoints, bounded exponential retry eligibility, and reopen/resume. A crash after tool commit retains the same action ID on retry.
- All 26 unittest tests pass, including fake-clock backoff, restart at every injected boundary, exhausted budgets, and conflicting run identity.
- Single executor per database only. Crash injection remains controlled exceptions; no distributed leases or OS/power-loss guarantees. Unknown attempts consume budget even if the process stopped before calling the tool.
- Next: bring persisted evidence into a visual offline demonstration. Provider adapters remain an explicit outstanding milestone.

## Visual product increment
- Added `python -m agentlab.dashboard`: freshly executed lookup, support-write, and durable-recovery experiments exported as a standalone HTML explorer and JSON evidence.
- Added comparison cards, suite/outcome filters, attempt timelines, expandable final-state evidence, and evidence download. Included a real browser screenshot and an expanded front-page README with a two-minute walkthrough.
- Added fixed read-only HTTP routes and defensive rendering: escaped JSON embedding, text-only rendering of trace values, no user-controlled filesystem mapping.
- All 29 unittest tests passed. Browser validation in the installed Chromium/Playwright checked 12 initial lookup cards, 7 failed cards, recovery navigation, replay evidence, JSON download, 4 support fixtures, 390px layout without horizontal overflow, and zero JavaScript errors.
- Initial export test exposed tuple/list JSON round-trip differences; comparison now uses the JSON representation. File navigation was disallowed by this machine's browser policy; browser checks used the supported local HTTP server.
- Milestone 5 has an offline demonstrable slice; it is not declared fully complete. Cross-run history and latency/cost comparison remain limited; missing cost is explicitly unavailable. Milestone 4 provider/replay adapters remain outstanding. No remote CI, public hosting, live models, or paid APIs were used.
- Next: provider-neutral offline replay and held-out fixtures, then cross-run history and CI/release validation. Continue tested feature-branch pushes without merging main.

## Offline adapter increment
- Added a provider-neutral decision protocol, bounded synthetic tool dispatcher, authored replay adapter, and separate heldout replay fixture split with source fingerprints.
- All 35 tests passed; `python -m agentlab.adapters` completed with 2/4 fixtures passing. False-finish and exhausted-budget fixtures intentionally remain failures; no model metrics are claimed.
- Tests cover unsupported tool rejection, budget enforcement, replay idempotency, independent grading, adapter mutation isolation, and invalid inputs.
- No live provider implementation, credentials, or paid API calls. See ADAPTERS.md for the supported contract and precise heldout limitation.

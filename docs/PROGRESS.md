# Progress

## Current release
Offline portfolio MVP on `codex/reliability-portfolio`, stacked on the unmerged
foundation and subsequent feature branches. Nothing merged into main. See
[RELEASE.md](RELEASE.md) for the 16/20 scope checklist, demo, and resume wording.
This is scope tracking, not a model-quality or production-readiness score.

## Implemented
- Six versioned lookup fixtures, strict scenario validation, source fingerprints,
  deterministic seeded schedules, bounded scripted policies, and per-attempt traces.
- SQLite synthetic orders/support tickets, atomic action writes, stable idempotency
  keys, conflict handling, replay and duplicate-intent evidence.
- Controlled exceptions before writing and on both sides of acknowledgment;
  independent final-state grading with a separate read-only database connection.
- SQLite intent/attempt checkpoints, executor reopen/resume, stable action identity,
  bounded budgets, and exponential retry eligibility with fake-clock tests.
- Provider-neutral decision protocol, allowlisted synthetic tool dispatcher,
  authored offline replay, and a separate versioned heldout fixture split.
- SQLite report history, validated immutable run IDs, fixed read-only APIs, visual
  active/reference comparison, local elapsed-time and call-count evidence,
  filters, expandable traces, JSON downloads, and a portable offline HTML report.
- Versioned exact behavioral regression gate; tests prove extra calls, duplicate
  writes, hidden expected failures, and lost resume completion are rejected.
- One-command `python -m agentlab.verify`, GitHub Actions configuration for
  Python 3.11–3.13 and optional browser acceptance, downloadable workflow artifacts,
  architecture diagram, real screenshot, demo walkthrough, and resume notes.

## Validation executed
- `python -m agentlab.verify --output artifacts/portfolio`: all 41 tests passed;
  fresh offline experiments completed and versioned regression gate passed.
- Lookup: scripted baseline 1/6, retry/validate 4/6. Support writes: 4/4.
  Offline replay: 2/4; false-finish and exhausted-budget fixtures intentionally fail.
- `python -m tools.browser_smoke --screenshot docs/images/dashboard.png`:
  passed active/reference selection, lookup and replay filters, recovery evidence,
  JSON download, mobile overflow check, and zero JavaScript errors.
- Clean staged-source export: full verification and browser acceptance passed
  without the original checkout's ignored artifacts or databases.
- `git diff --check`: passed.

## Limits and remaining work
No live models, paid APIs, production data, or cost/token measurements. Replay
transcripts are authored synthetic fixtures, not model recordings; the heldout
split is not a statistical model evaluation. Local timing is not API latency.
Crash exceptions do not establish OS/power-loss recovery; execution is single
executor per database, with no distributed leases. The support model permits one
ticket per order. Exports/API snapshots show at most the most recent 20 runs.

Remote GitHub Actions results have not been observed. API requests/PR creation
have returned Forbidden while native Git push works. Workflow configuration and
local checks must not be described as remote CI passing. Live-provider integration,
actual held-out model evaluation, and reviewed default-branch publication remain
outstanding. No public deployment was performed.

Next: observe remote CI after access is restored, review and publish the existing
product branches, then add opt-in live adapters only with an explicit budget and
credentials. No further feature expansion is needed for the offline resume demo.

## Process-crash testing addition
- Added SQLite WAL/FULL write connections and boundary instrumentation around writes and policy acknowledgment.
- Added real subprocess termination and new-process resume at before-write, during-transaction, committed-before-ack, and ack-before-policy-checkpoint boundaries.
- All 44 tests passed; the POSIX harness confirmed SIGKILL exits, rollback of uncommitted state, preserved identity, intact SQLite, and one final ticket/action.
- Added `python -m agentlab.process_crash` and CRASH_TESTING.md. These checks do not claim host power-loss or distributed execution guarantees.

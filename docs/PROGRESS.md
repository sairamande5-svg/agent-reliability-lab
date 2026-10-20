# Progress

## Current release
Portfolio hardening on `codex/reliability-public-demo`: actual process-kill
recovery, Hypothesis-generated invariant tests, and a verified static Pages build.
The earlier offline MVP was merged externally into main in PR #6. These additions
are pending review; this work does not merge main. See [RELEASE.md](RELEASE.md)
and [DEPLOYMENT.md](DEPLOYMENT.md) for evidence, demo instructions, and resume wording.

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
- `.venv-testing/bin/python -m agentlab.verify --properties`: all 47 standard tests
  and three Hypothesis property tests passed; fresh experiments and baseline v2 passed.
- Lookup: scripted baseline 1/6, retry/validate 4/6. Support writes: 4/4.
  Offline replay: 2/4; false-finish and exhausted-budget fixtures intentionally fail.
  Actual process-kill recovery: 4/4, with SIGKILL exit status verified on Linux.
- `python -m tools.browser_smoke --static --screenshot docs/images/dashboard.png`:
  passed active/reference selection, lookup and replay filters, recovery evidence,
  actual process-kill evidence, JSON download, mobile overflow check, and zero JavaScript errors.
- Clean staged-source export: all standard/property tests, regression gate, and
  static build passed without the original checkout's artifacts or databases.
  Browser acceptance passed separately against freshly generated static content.
- `git diff --check`: passed.

## Limits and remaining work
No live models, paid APIs, production data, or cost/token measurements. Replay
transcripts are authored synthetic fixtures, not model recordings; the heldout
split is not a statistical model evaluation. Local timing is not API latency.
Actual worker termination is verified at synchronized boundaries, not host power loss; execution is single
executor per database, with no distributed leases. The support model permits one
ticket per order. Exports/API snapshots show at most the most recent 20 runs.

Remote GitHub Actions results have not been observed. API requests/PR creation
have returned Forbidden while native Git push works. Workflow configuration and
local checks must not be described as remote CI passing. Live-provider integration,
actual held-out model evaluation, and reviewed publication of the new additions
remain outstanding. Pages activation and live-site confirmation are blocked by API/proxy access.

Next: enable Pages in repository settings and observe deployment/CI, then review
the new feature branch. Opt-in live adapters still require an explicit budget and credentials.

## Process-crash testing addition
- Added SQLite WAL/FULL write connections and boundary instrumentation around writes and policy acknowledgment.
- Added real subprocess termination and new-process resume at before-write, during-transaction, committed-before-ack, and ack-before-policy-checkpoint boundaries.
- All 44 tests passed; the POSIX harness confirmed SIGKILL exits, rollback of uncommitted state, preserved identity, intact SQLite, and one final ticket/action.
- Added `python -m agentlab.process_crash` and CRASH_TESTING.md. These checks do not claim host power-loss or distributed execution guarantees.

## Property-testing addition
- Added pinned optional Hypothesis dependencies, a stateful reference-model test, generated reopen/retry schedules, and generated persisted-budget checks.
- `agentlab.verify --properties` passed all 44 standard tests, all three generated property tests, and the existing regression gate. The optional test environment also passed `pip check`.
- Added explicit property verification to the CI matrix. Missing Hypothesis fails an explicitly requested property run; no silent skips or inflated example counts.
- Added PROPERTY_TESTING.md with settings, invariants, reproducibility, and limits. Actual process kills remain separate from the generated exception schedules.

## Static demonstration and evidence addition
- Dashboard now exposes the four actual process-kill scenarios, including signals, WAL journal mode, integrity checks, before-resume state, and final-state evidence.
- Added baseline v2 for process-kill invariants. Confirmed every pre-existing behavioral expectation exactly matches retained v1; no failures were weakened or hidden.
- Added a static-only builder with two fresh sample runs, source-SHA metadata, public-file allowlist, and checksums. Existing private files cause a refusal; databases are not published or deleted.
- All 47 standard tests and three Hypothesis property tests passed, along with the regression gate. Static browser acceptance passed under `/agent-reliability-lab/` with new process-kill evidence, filters, export, and mobile checks. Updated the real screenshot.
- Added a Pages build/deploy workflow and deployment instructions. Both workflow YAML files parse locally. Remote CI/deployment has not been observed.
- Discovered the previous portfolio release was merged externally into main (PR #6); these additions stay on `codex/reliability-public-demo` pending review. No merge was performed here.
- GitHub Pages API returns Forbidden; access to the Pages hostname fails with a proxy 403. Pages activation and confirmation of a public demo remain external blockers. The artifact is built and locally verified, not claimed live.

## Publication confirmed
- The repository administrator enabled Pages and permitted the feature branch while retaining the main-branch rule.
- Reran failed deployment; workflow 39508786286 attempt 3 succeeded. GitHub deployment 7213003537 reports success at https://sairamande5-svg.github.io/agent-reliability-lab/.
- All ten PR #8 checks passed for 3c091fa, including the remote Python matrix, browsers, build, and deployment. The release checklist is now 17/20.
- Added the confirmed demo URL to the README. Direct hosted browsing remains blocked by the execution environment proxy; local static browser acceptance and GitHub deployment status are the available evidence.
- New additions remain unmerged; no merge was performed.

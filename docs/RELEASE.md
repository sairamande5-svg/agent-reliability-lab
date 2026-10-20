# Offline portfolio release

## Release scope: 16 of 20 checks complete (80%)

This is an equally weighted scope checklist, not a product-quality metric or an
estimate of remaining effort. The offline MVP can be demonstrated now. Live model
work and publication remain explicitly incomplete.

| Check | Evidence/status |
| --- | --- |
| Six controlled lookup failure fixtures | Verified by tests and fresh reports |
| Strict versioned scenario loading and seeded schedules | Verified by scenario tests |
| Synthetic order/support database | Verified by SQLite tests |
| Idempotent writes and duplicate-intent detection | Verified by replay/conflict tests |
| Before-write and acknowledgment-boundary crashes | Verified at all injected boundaries |
| Independent final business-state grading | Verified, including deliberately wrong state |
| Persisted intent, action identity, and restart/resume | Verified after executor reopening |
| Bounded retry backoff | Verified with fake clock |
| Provider-neutral tool decision interface | Implemented and tested |
| Separate authored offline replay fixture split | Executed; 2/4 pass, 2 intentional failures |
| Decision/tool budgets and honest absent usage metadata | Tested; no invented cost or tokens |
| Persisted run history and comparison | SQLite tests and browser checks |
| Visual filters, attempt evidence, and JSON export | Browser acceptance passed |
| Safe trace rendering and fixed read-only API routes | Injection/traversal tests passed |
| Versioned behavioral regression gate | Passing; tests prove regressions are rejected |
| Reproducible offline demo, documentation, and clean-source verification | Verified locally; 41 tests and browser acceptance |
| Remote GitHub Actions matrix passes | Pending: workflow configured, API access denied |
| Opt-in live provider implementation | Deferred; protocol/offline adapter ready |
| Actual held-out live-model evaluation with measured usage | Deferred; requires an explicit budget and credentials |
| Reviewed default-branch publication | Pending; feature branches pushed, nothing merged |

The test suite has 41 tests. A failing fixture is not a failing test: false finish,
persistent timeout, and exhausted-budget fixtures are expected behavioral outcomes
and stay visible in reports. No CI badge or production reliability number is claimed.

## One-command verification

From a clean source checkout, run:

```sh
python -m agentlab.verify
```

This runs the entire unittest suite, executes fresh offline experiments, checks the
versioned baseline, and writes a portable dashboard and JSON evidence to
`artifacts/portfolio/`. A test or gate failure exits nonzero. To demonstrate:

```sh
python -m agentlab.dashboard --output artifacts/demo --run-id reference
python -m agentlab.dashboard --output artifacts/demo --run-id candidate --serve
```

Run IDs are immutable; pick new IDs on later runs. The default generated ID is
unique when `--run-id` is omitted. Select the active/reference runs in the UI.
Compare local timings only within their stated fixture context; they are not API
latency or a performance benchmark across machines. The export contains at most
the most recent 20 runs; SQLite keeps earlier records. Regenerating the report
refreshes the server's snapshot; this is a local, read-only demonstration service.

Optional browser acceptance (not required to run the application):

```sh
python -m pip install playwright==1.55.0
python -m playwright install chromium
python -m tools.browser_smoke
```

The GitHub Actions workflow runs offline verification on Python 3.11–3.13 and a
separate browser job, then uploads HTML/JSON and screenshot artifacts. Workflow
configuration is committed; a remote green run has not been observed. It neither
uses paid model APIs nor reads model secrets. Public hosting is not configured.

## Regression baseline

`baselines/offline-v1.json` records exact fixture outcomes, call counts, source
fingerprints, duplicate evidence, and durable completion state. Timing, temporary
paths, and random action identifiers are excluded. The gate preserves expected
failures as well as successes. Review behavioral/source changes deliberately
before updating the baseline; do not refresh it just to make a regression pass.

## Resume wording supported by current evidence

> Built Agent Reliability Lab, an offline Python/SQLite evaluation workbench for
> tool-using agents, featuring crash injection, idempotent writes, durable retry
> checkpoints, independent database-state validation, and an interactive results
> dashboard; validated with 41 automated tests and browser acceptance checks.

Do not describe the project as production deployed, live-model evaluated, or
proven to improve real-world reliability. Describe CI as configured until a
successful remote run is observed. Link the feature branch containing the product
until a reviewed merge makes it visible on the default repository page.

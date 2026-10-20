# Offline portfolio release

## Release scope: 17 of 20 checks complete (85%)

This is an equally weighted scope checklist, not a product-quality metric or an
estimate of remaining effort. The offline MVP can be demonstrated now. Live model
work and reviewed default-branch publication of the latest additions remain incomplete.

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
| Reproducible offline demo, documentation, and clean-source verification | Verified locally; 47 standard tests plus three property tests and browser acceptance |
| Remote GitHub Actions matrix passes | Confirmed passing on Python 3.11–3.13; all ten PR checks passed for 3c091fa |
| Opt-in live provider implementation | Deferred; protocol/offline adapter ready |
| Actual held-out live-model evaluation with measured usage | Deferred; requires an explicit budget and credentials |
| Reviewed default-branch publication | New additions pending review; earlier MVP merged externally |

The suite has 47 standard tests plus three explicitly requested Hypothesis property tests. A failing fixture is not a failing test: false finish,
persistent timeout, and exhausted-budget fixtures are expected behavioral outcomes
and stay visible in reports. No CI badge or production reliability number is claimed.

## One-command verification

From a clean source checkout, run:

```sh
python -m agentlab.verify
```

This runs the standard unittest suite, executes fresh offline experiments, checks the
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
separate browser job, then uploads HTML/JSON and screenshot artifacts. Remote verification and Pages deployment have passed. It neither
uses paid model APIs nor reads model secrets. A verified-build Pages workflow is configured; GitHub confirms publication at https://sairamande5-svg.github.io/agent-reliability-lab/ See DEPLOYMENT.md.

## Regression baseline

`baselines/offline-v2.json` extends the retained v1 baseline with real process-kill evidence and records exact fixture outcomes, call counts, source
fingerprints, duplicate evidence, and durable completion state. Timing, temporary
paths, and random action identifiers are excluded. The gate preserves expected
failures as well as successes. Review behavioral/source changes deliberately
before updating the baseline; do not refresh it just to make a regression pass.

To include the generated property suite, install `requirements-test.txt` and use
`python -m agentlab.verify --properties` in that environment. These checks are
explicitly requested by CI. See PROPERTY_TESTING.md for reproducible setup.

## New engineering evidence

Real worker kills at four synchronized boundaries recover with one final ticket
and one action identity under SQLite WAL/FULL. Generated state-machine tests
compare database contents to an independent model through crashes, conflicts,
replays, and reopening. The Pages build publishes only static synthetic evidence;
local browser tests passed under the repository subpath. GitHub reports successful deployment; direct hosted browser verification is still
blocked by this environment's network proxy.

## Resume wording supported by current evidence

> Built a Python/SQLite agent reliability workbench with WAL-backed durable
> execution, SIGKILL recovery verification, Hypothesis state-machine testing,
> idempotent tool actions, and an interactive execution-evidence dashboard.

Do not describe the project as production deployed, live-model evaluated, or
proven to improve real-world reliability. Remote CI and deployment have now been observed passing. Link the feature branch for the newest additions until a reviewed merge makes them visible on the default repository page. The earlier offline MVP has already been merged externally.

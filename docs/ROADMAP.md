# Roadmap

1. Deterministic foundation (complete)
   - Six named failure fixtures; bounded retry policy; JSON traces; independent outcome check; tests.
   - Implemented configurable versioned scenario files, strict validation, and deterministic seeded fault schedules (see SCENARIOS.md).
2. Stateful tool environment (complete)
   - Synthetic order/support database; idempotent writes; duplicate-action detection.
   - Inject crashes before and after write acknowledgment. Verify final state, not returned text.
3. Durable execution (complete; single executor)
   - SQLite checkpoints and restart/resume; bounded backoff with fake-clock tests.
   - Verify resumed runs preserve action identity and do not duplicate writes.
4. Real agent adapter (offline contract/replay complete; live provider deferred)
   - Provider-neutral adapter and offline replay adapter first; opt-in live provider integration.
   - Fixed task budgets; token/cost metadata only when actually available; held-out scenarios.
   - Keep scripted-policy results separate from model-driven results.
5. Results API and dashboard (offline scope complete; missing live cost explicitly unavailable)
   - Compare runs, inspect attempt traces, show failures and latency/cost tradeoffs.
   - Escape untrusted trace content. Validate filesystem identifiers and API inputs.
6. CI and portfolio release (local checks complete; remote CI/publication pending)
   - GitHub Actions test and offline benchmark workflow; downloadable reports.
   - Regression gates against versioned baselines; model evaluation only with explicit secrets and budget.
   - Reproducible commands, architecture diagram, demo, limitations, and measured results.

Completion: clean-checkout offline run succeeds; durable recovery and idempotency tests pass; dashboard displays persisted evidence; CI passes; optional model evaluation is documented honestly.


Offline portfolio scope: see [RELEASE.md](RELEASE.md) for 16/20 verified scope checks and the explicit remaining work. No full-roadmap completion claim is made.

## Approved portfolio hardening additions
- Real subprocess kills at four write/acknowledgment boundaries with WAL/FULL and independent recovery verification: implemented and locally verified.
- Hypothesis state-machine/reference-model and generated schedule/budget checks: implemented and locally verified.
- Static Pages artifact, publication workflow, and repository-subpath browser acceptance: implemented and locally verified; Pages activation and a confirmed public URL remain blocked by GitHub API/proxy access.
These additions do not introduce paid model APIs or change the outstanding live-provider scope.

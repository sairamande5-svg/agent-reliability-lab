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
4. Real agent adapter
   - Provider-neutral adapter and offline replay adapter first; opt-in live provider integration.
   - Fixed task budgets; token/cost metadata only when actually available; held-out scenarios.
   - Keep scripted-policy results separate from model-driven results.
5. Results API and dashboard (offline demo implemented; cross-run history outstanding)
   - Compare runs, inspect attempt traces, show failures and latency/cost tradeoffs.
   - Escape untrusted trace content. Validate filesystem identifiers and API inputs.
6. CI and portfolio release
   - GitHub Actions test and offline benchmark workflow; downloadable reports.
   - Regression gates against versioned baselines; model evaluation only with explicit secrets and budget.
   - Reproducible commands, architecture diagram, demo, limitations, and measured results.

Completion: clean-checkout offline run succeeds; durable recovery and idempotency tests pass; dashboard displays persisted evidence; CI passes; optional model evaluation is documented honestly.


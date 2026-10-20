# Adapter contract and offline replay

`agentlab.adapters.Adapter` is a provider-neutral Python protocol. Implement
`decide(task, observations) -> Decision` to return `lookup_order`, `open_ticket`,
or `finish`. Arguments must exactly match the tool's fields. Unsupported tools
and malformed decisions are recorded and consume decision budget; arbitrary
code, URLs, and shell commands are never dispatched.

`evaluate` accepts a fixed 1–20 decision budget, runs synthetic tools against an
isolated database, and grades business state independently. Tool calls and
model decisions are counted separately. A finish decision is not success by
itself. Providers must enforce their own transport timeouts; the harness does
not sandbox untrusted Python adapter implementations.

`ReplayAdapter` replays authored synthetic decisions. It is an offline adapter
integration test, not captured live-model behavior. `tokens` and `cost_usd` are
null because no usage was measured. A future provider adapter should record
usage only from actual responses, require explicit credentials and budget,
and remain opt-in. No live provider integration is included in this release.

Run `python -m agentlab.adapters`. The versioned
`scenarios/replay-heldout-v1.json` suite is separate from the development lookup
fixtures. It exercises new orders/reasons, acknowledgment loss, false finish,
and budget exhaustion. It intentionally includes failures. “Heldout” labels
this fixture split only; no model was tuned or evaluated and it is not evidence
of statistical generalization. Reports include a source SHA-256 fingerprint.

The loader rejects duplicate JSON keys, oversized documents/case sets, duplicate
case names, unsupported schema versions, and invalid budgets or fault schedules.

# Property-based fault testing with Hypothesis

The application remains standard-library-only. Install the pinned optional test
packages in a virtual environment to run generated tests:

```sh
python -m venv .venv-testing
.venv-testing/bin/python -m pip install -r requirements-test.txt
.venv-testing/bin/python -m agentlab.verify --properties
```

The property suite is separate from ordinary unittest discovery so missing
Hypothesis cannot silently skip checks. `--properties` explicitly runs it and
fails if its dependency is absent. The GitHub Actions verification matrix installs
these dependencies and requests property checks on every configured Python version.

Three generated tests complement the deterministic suite:

- A state machine interleaves writes with three action IDs, conflicting reasons,
  crash points, and connection reopening. After every rule, an independent SQL
  read checks tickets, action bindings, and duplicate events against a separate
  in-memory model. It is configured for up to 50 examples of 30 rules each.
- Generated fault schedules of up to eight injected boundaries exercise reopened
  durable executors. A final healthy attempt must leave one ticket and one action
  identity, never more than the persisted budget. Up to 100 examples are requested.
- Generated budgets from 1–10 test persistent failures across reopening: attempts
  must never exceed budget, and the final state must be exhausted. Up to 50
  examples are requested; the finite input space may require fewer distinct cases.

The settings use deterministic generation (`derandomize=True`) for repeatability,
while Hypothesis still shrinks a failing sequence to a smaller counterexample.
Counts above are configured bounds, not a claim that every possible schedule
was explored. Preserve a failing reproduction before changing a test or policy.
Generated crashes here use exceptions; actual process-kill recovery is tested
separately by the synchronized subprocess harness in CRASH_TESTING.md.

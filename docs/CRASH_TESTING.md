# Real process-crash recovery

Run `python -m agentlab.process_crash`. The experiment creates a synthetic order
and durable intent in SQLite, starts a real Python worker, waits for an explicit
boundary handshake over a pipe, kills that worker, and resumes with a new process.
On POSIX the runner verifies the killed worker's exit status is `-SIGKILL`.
On Windows `Popen.kill` uses TerminateProcess and the report labels that separately.
No sleeps are used to guess where execution stopped. Timeouts fail the experiment
and always reap the worker; only the child started by the experiment is killed.

| Kill boundary | Expected database before resume |
| --- | --- |
| `before_write` | Attempt checkpoint exists; no ticket/action |
| `during_write` | Uncommitted ticket/action roll back; no ticket/action |
| `before_ack` | Ticket/action committed; acknowledgment not returned |
| `after_ack` | Tool returned; policy completion not checkpointed |

The worker blocks inside the boundary callback until the parent kills it. This
is stronger than catching a simulated Python exception: cleanup handlers do not
run in the killed worker. SQLite write connections use WAL journaling,
`synchronous=FULL`, and foreign-key enforcement. The parent checks final business
state through an independent connection, action identity, attempt count, and
`PRAGMA integrity_check` after resuming. The report retains exit status, journal
mode, pre-resume state, recovered checkpoint, and final-state evidence.

Boundary callbacks are local instrumentation for the experiment, not tools an
adapter can request. Existing exception-based fixtures remain useful fast unit
checks and are labeled separately. This verifies local process termination at
selected boundaries; it does not establish host power-loss durability, distributed
exactly-once execution, or behavior under disk failure. One executor per database
is still the supported execution model.

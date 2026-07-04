# Executor Abstraction

The harness uses an executor abstraction to isolate task execution from runner
state management. TASK-008 keeps execution fully simulated. The runner uses
`MockExecutor`; it does not call Gemini, Codex, Claude, shells, or any other
external agent process.

## BaseExecutor

`executors/base.py` defines the minimum interface:

- `name`
- `role`
- `execute(task, context)`

`execute` receives task data and a context dictionary, then returns a result
dictionary.

## MockExecutor

`executors/mock.py` implements the interface with deterministic simulated
execution. It can be configured with:

- `should_succeed`
- `output`
- `failure_reason`
- `role`

Successful execution returns `success: True` and textual output. Controlled
failure returns `success: False`, textual output, and an error string.

## Runner Logs

The runner records executor events in the existing harness logs:

- `executor_started`
- `executor_completed`
- `executor_failed`

Executor failure is routed through the existing review flow, preserving the
state path `pending -> running -> review -> failed`. Default mock execution
succeeds, so existing review behavior remains unchanged.

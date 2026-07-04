# Executor Registry

`executor_registry.py` loads `config/executors.json`, validates configured
executors, and resolves the executor requested by a task. TASK-009 keeps all
execution simulated: the only instantiated executor is `MockExecutor`. CLI
entries may be present in configuration, but disabled or unsupported runtime
entries fall back to mock execution and are never launched as subprocesses.

## Configuration Format

The supported file format is:

```json
{
  "executors": {
    "mock_default": {
      "type": "mock",
      "role": "harness",
      "enabled": true,
      "should_succeed": true,
      "output": "optional mock output",
      "failure_reason": "optional mock failure reason"
    },
    "codex_s10": {
      "type": "cli",
      "container": "ubuntu-codex",
      "command": "codex",
      "enabled": false
    }
  }
}
```

Required top-level field:

- `executors`: object keyed by executor name

Supported executor fields:

- `type`: `mock` or `cli`; defaults to `mock`
- `role`: optional role used for role-based resolution
- `enabled`: optional boolean-like value; defaults to `true`
- `should_succeed`: optional mock success control
- `output`: optional mock output text
- `failure_reason`: optional mock failure text
- `command`: accepted for `cli` metadata validation only
- `container`: accepted as metadata

## Resolution

The runner asks the registry for an executor using task metadata:

- by name: `executor` or `executor_name`
- by role: `executor_role` or `role`

Resolution prefers an explicit name, then role. If the selected executor is
missing, disabled, invalid for simulated execution, or the registry cannot load
valid configuration, the registry returns a `MockExecutor` fallback.

## Logs

The runner records registry activity in existing harness logs:

- `executor_registry_loaded`
- `executor_resolved`
- `executor_fallback_used`
- `executor_registry_error`

No registry path executes Gemini, Codex, Claude, or any external agent process.

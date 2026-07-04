# Runtime Configuration

`runtime_config.py` provides safe runtime defaults and explicit real-executor policy helpers.

## Defaults

- `execution_mode = dry_run`
- `dry_run = true`
- `enable_real_executors = false`

## Policy Helpers

- `allows_real_execution()` reports whether the global runtime is real.
- `allows_real_executor(name)` reports whether a named real executor is feature-flagged.
- Missing `config/runtime.json` is allowed, but it is treated as a warning and safe defaults remain in force.

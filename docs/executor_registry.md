# Executor Registry

`executor_registry.py` loads `config/executors.json` and resolves executors by name or role.

## Policy

- `mock`: simulated execution only.
- `dry_run`: safe executor path, still non-real.
- `real`: policy-gated resolution only; phase 3.1 does not launch real executors.

## Real Executor Policy

A real executor is only policy-eligible when all of the following are true:

- `runtime_config.execution_mode == "real"`
- `runtime_config.enable_real_executors == true`
- The executor-specific feature flag is enabled

If any requirement fails, the registry returns a blocked resolution instead of falling back silently to `MockExecutor`.

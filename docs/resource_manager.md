# Resource Manager

`resource_manager.py` manages runtime-local directories under `runtime/`:

- `runtime/temp/`
- `runtime/locks/`
- `runtime/state/`

It creates an isolated temp directory per `execution_id`, records paths on the
`ExecutionContext`, and refuses cleanup outside runtime temp.

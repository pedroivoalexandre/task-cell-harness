# Resource Manager

`resource_manager.py` manages runtime-local directories under the project root.

## Guarantees

- `project_root` is required.
- `runtime/`, `runtime/temp/`, `runtime/locks/`, and `runtime/state/` must stay inside `project_root`.
- Workspace creation validates the execution id and rejects traversal attempts.
- Cleanup refuses any path outside `project_root` and any path outside `runtime/temp`.

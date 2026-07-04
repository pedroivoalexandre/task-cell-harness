import shutil
from pathlib import Path


class ResourceManager:
    def __init__(self, root=Path("runtime"), project_root=None):
        if project_root is None:
            raise ValueError("project_root is required")
        self.project_root = Path(project_root).resolve()
        self.root = self._resolve_within_project(root, "runtime root")
        self.temp = self._resolve_within_project(self.root / "temp", "runtime temp")
        self.locks = self._resolve_within_project(self.root / "locks", "runtime locks")
        self.state = self._resolve_within_project(self.root / "state", "runtime state")

    def _resolve_within_project(self, candidate, label):
        path = Path(candidate).resolve()
        try:
            path.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(f"{label} must stay within project_root") from exc
        return path

    def _safe_component(self, value, label):
        component = str(value or "")
        if not component or component in (".", "..") or Path(component).name != component:
            raise ValueError(f"invalid {label}")
        return component

    def ensure_directories(self):
        for directory in (self.temp, self.locks, self.state):
            directory.mkdir(parents=True, exist_ok=True)

    def prepare_execution(self, execution_context):
        self.ensure_directories()
        execution_id = self._safe_component(execution_context.execution_id, "execution_id")
        workspace = self._resolve_within_project(self.temp / execution_id, "runtime workspace")
        workspace.mkdir(parents=True, exist_ok=True)
        execution_context.log_context["runtime_temp_dir"] = str(workspace)
        execution_context.log_context["runtime_lock_dir"] = str(self.locks)
        execution_context.log_context["runtime_state_dir"] = str(self.state)
        return workspace

    def cleanup_execution(self, execution_context):
        workspace = Path(execution_context.log_context.get("runtime_temp_dir", ""))
        if not workspace:
            return False
        resolved = workspace.resolve()
        try:
            resolved.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError("refusing to cleanup outside project_root") from exc
        try:
            resolved.relative_to(self.temp)
        except ValueError as exc:
            raise ValueError("refusing to cleanup outside runtime temp") from exc
        if workspace.exists():
            shutil.rmtree(workspace)
            return True
        return False

    def retention_days(self, runtime_config):
        return getattr(runtime_config, "artifact_retention_days", None)

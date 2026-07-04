import shutil
from pathlib import Path


class ResourceManager:
    def __init__(self, root=Path("runtime"), project_root=Path(".")):
        self.root = Path(root)
        self.project_root = Path(project_root).resolve()
        self.temp = self.root / "temp"
        self.locks = self.root / "locks"
        self.state = self.root / "state"

    def ensure_directories(self):
        for directory in (self.temp, self.locks, self.state):
            directory.mkdir(parents=True, exist_ok=True)

    def prepare_execution(self, execution_context):
        self.ensure_directories()
        workspace = self.temp / execution_context.execution_id
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
        allowed_root = self.temp.resolve()
        if allowed_root not in resolved.parents and resolved != allowed_root:
            raise ValueError("refusing to cleanup outside runtime temp")
        if workspace.exists():
            shutil.rmtree(workspace)
            return True
        return False

    def retention_days(self, runtime_config):
        return getattr(runtime_config, "artifact_retention_days", None)

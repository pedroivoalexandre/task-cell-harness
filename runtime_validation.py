import json
from pathlib import Path

from executor_registry import load_executor_registry
from runtime_config import RuntimeConfig

REQUIRED_DIRS = ("tasks", "reports", "logs", "artifacts", "config", "docs", "executors")


class RuntimeValidator:
    def __init__(self, root=Path(".")):
        self.root = Path(root)

    def validate(self):
        checks = []
        checks.extend(self._check_directories())
        checks.append(self._check_executor_config())
        checks.append(self._check_runtime_config())
        checks.append(self._check_dry_run_safety())
        checks.append(self._check_project_integrity())
        ok = all(check["ok"] for check in checks)
        return {"ok": ok, "checks": checks}

    def write_report(self, path):
        result = self.validate()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Runtime Validation", "", f"Result: {'OK' if result['ok'] else 'FAILED'}", ""]
        for check in result["checks"]:
            status = "OK" if check["ok"] else "FAILED"
            lines.append(f"- {check['name']}: {status} - {check['message']}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return result

    def _check_directories(self):
        return [
            {
                "name": f"directory:{directory}",
                "ok": (self.root / directory).exists(),
                "message": str(self.root / directory),
            }
            for directory in REQUIRED_DIRS
        ]

    def _check_executor_config(self):
        registry = load_executor_registry(self.root / "config" / "executors.json")
        return {
            "name": "config/executors.json",
            "ok": not registry.errors,
            "message": "; ".join(registry.errors) if registry.errors else "valid",
        }

    def _check_runtime_config(self):
        try:
            RuntimeConfig.load(self.root / "config" / "runtime.json").validate()
            return {"name": "runtime_config", "ok": True, "message": "safe defaults valid"}
        except Exception as exc:
            return {"name": "runtime_config", "ok": False, "message": str(exc)}

    def _check_dry_run_safety(self):
        config = RuntimeConfig.load(self.root / "config" / "runtime.json")
        return {
            "name": "dry_run_safety",
            "ok": not config.allows_real_execution(),
            "message": "real executors blocked" if not config.allows_real_execution() else "real execution enabled",
        }

    def _check_project_integrity(self):
        required = ("runner.py", "scheduler.py", "state_machine.py", "execution_context.py")
        missing = [name for name in required if not (self.root / name).exists()]
        return {
            "name": "project_integrity",
            "ok": not missing,
            "message": "missing: " + ", ".join(missing) if missing else "required files present",
        }

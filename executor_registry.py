import json
from pathlib import Path

from executors.mock import MockExecutor

DEFAULT_CONFIG_PATH = Path("config") / "executors.json"
SUPPORTED_TYPES = ("mock", "cli")
MOCK_NAMES = ("mock", "mock_executor")


class ExecutorRegistryError(ValueError):
    pass


def boolean_setting(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off"):
            return False
    return bool(value)


class ExecutorRegistry:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.executors = {}
        self.errors = []

    def load(self):
        self.executors = {}
        self.errors = []
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.errors.append(f"executor config not found: {self.config_path}")
            return self
        except json.JSONDecodeError as exc:
            self.errors.append(
                f"invalid executor config JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"
            )
            return self

        configured = raw.get("executors") if isinstance(raw, dict) else None
        if not isinstance(configured, dict):
            self.errors.append("executor config must contain an executors object")
            return self

        for name, config in configured.items():
            error = self._validate_entry(name, config)
            if error:
                self.errors.append(error)
                continue

            normalized = dict(config)
            normalized["name"] = name
            normalized["type"] = normalized.get("type", "mock")
            normalized["enabled"] = boolean_setting(normalized.get("enabled"), default=True)
            self.executors[name] = normalized
        return self

    def _validate_entry(self, name, config):
        if not isinstance(name, str) or not name.strip():
            return "executor name must be a non-empty string"
        if not isinstance(config, dict):
            return f"executor {name} must be an object"

        executor_type = config.get("type", "mock")
        if executor_type not in SUPPORTED_TYPES:
            return f"executor {name} has unsupported type: {executor_type}"

        role = config.get("role")
        if role is not None and (not isinstance(role, str) or not role.strip()):
            return f"executor {name} role must be a non-empty string"

        if executor_type == "cli":
            command = config.get("command")
            if command is not None and (not isinstance(command, str) or not command.strip()):
                return f"executor {name} command must be a non-empty string"
        return None

    def resolve(self, name=None, role=None, task=None):
        task = task or {}
        selected = None
        reason = "fallback"
        fallback = False

        if name:
            selected = self.executors.get(name)
            reason = "name"
        if selected is None and role:
            selected = self._find_by_role(role)
            reason = "role"

        if not self._is_usable(selected):
            selected = self._mock_config(role=role or task.get("role"), name=name)
            fallback = True
            reason = "fallback"

        executor = self._build_mock_executor(selected, task)
        return {
            "executor": executor,
            "config": selected,
            "fallback": fallback,
            "reason": reason,
        }

    def _find_by_role(self, role):
        for config in self.executors.values():
            if config.get("role") == role:
                return config
        return None

    def _is_usable(self, config):
        if not config or not config.get("enabled", True):
            return False
        return config.get("type") == "mock" or config.get("name") in MOCK_NAMES

    def _mock_config(self, role=None, name=None):
        return {
            "name": "mock",
            "type": "mock",
            "role": role or "mock",
            "enabled": True,
            "fallback_for": name,
        }

    def _build_mock_executor(self, config, task):
        return MockExecutor(
            role=task.get("role") or config.get("role") or "mock",
            should_succeed=mock_success_setting(task, config),
            output=task.get("mock_executor_output") or config.get("output"),
            failure_reason=(
                task.get("mock_executor_failure_reason")
                or config.get("failure_reason")
            ),
        )


def mock_success_setting(task, config):
    for field in ("mock_executor_success", "mock_executor_should_succeed"):
        if field in task:
            return boolean_setting(task.get(field))
    if "should_succeed" in config:
        return boolean_setting(config.get("should_succeed"))
    return True


def load_executor_registry(config_path=DEFAULT_CONFIG_PATH):
    return ExecutorRegistry(config_path).load()

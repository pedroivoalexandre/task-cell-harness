import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


def boolean_setting(value, default=False):
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


@dataclass
class RuntimeConfig:
    execution_mode: str = "dry_run"
    dry_run: bool = True
    enable_real_executors: bool = False
    default_timeout_seconds: int = 300
    retry_policy: dict = field(default_factory=lambda: {"max_retries": 0, "backoff_seconds": 0})
    max_parallel_tasks: int = 1
    artifact_retention_days: int = 30
    log_level: str = "INFO"
    feature_flags: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path=None):
        config, _warnings = cls.load_with_warnings(path)
        return config

    @classmethod
    def load_with_warnings(cls, path=None):
        config = cls()
        warnings = []
        if path is None:
            return config, warnings

        path = Path(path)
        if not path.exists():
            warnings.append(f"runtime config not found: {path}; using safe defaults")
            return config, warnings

        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("runtime config must be a JSON object")

        data = asdict(config)
        data.update(raw)
        loaded = cls(**{key: data[key] for key in data if key in cls.__dataclass_fields__})
        loaded.validate()
        return loaded, warnings

    def validate(self):
        if self.execution_mode not in ("dry_run", "real"):
            raise ValueError("execution_mode must be dry_run or real")
        if self.execution_mode == "real" and not self.enable_real_executors:
            raise ValueError("real execution is blocked unless enable_real_executors is true")
        if not self.enable_real_executors:
            self.dry_run = True
            self.execution_mode = "dry_run"
        if self.default_timeout_seconds <= 0:
            raise ValueError("default_timeout_seconds must be positive")
        if self.max_parallel_tasks <= 0:
            raise ValueError("max_parallel_tasks must be positive")
        if self.artifact_retention_days < 0:
            raise ValueError("artifact_retention_days must be non-negative")
        return True

    def allows_real_execution(self):
        return self.execution_mode == "real" and self.enable_real_executors and not self.dry_run

    def real_executor_flags(self):
        flags = self.feature_flags or {}
        for key in ("real_executors", "executors"):
            nested = flags.get(key)
            if isinstance(nested, dict):
                return nested
        return {key: value for key, value in flags.items() if isinstance(value, (bool, str, int, float))}

    def allows_real_executor(self, executor_name):
        if not executor_name:
            return False
        return self.allows_real_execution() and boolean_setting(self.real_executor_flags().get(executor_name), default=False)

    def feature_flag_enabled(self, name, default=False):
        return boolean_setting((self.feature_flags or {}).get(name), default=default)

    def to_dict(self):
        return asdict(self)

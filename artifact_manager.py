import hashlib
import json
import shutil
from pathlib import Path
from uuid import uuid4

from execution_context import utc_now


class ArtifactManager:
    def __init__(self, root=Path("artifacts")):
        self.root = Path(root)

    def execution_dir(self, execution_context):
        return self.root / execution_context.task_id / execution_context.execution_id

    def index_path(self, execution_context):
        return self.execution_dir(execution_context) / "artifacts.json"

    def register_file(self, source_path, execution_context, name=None, kind="file"):
        source_path = Path(source_path)
        target_dir = self.execution_dir(execution_context)
        target_dir.mkdir(parents=True, exist_ok=True)

        artifact_name = name or source_path.name
        target_path = target_dir / artifact_name
        if source_path.resolve() != target_path.resolve():
            shutil.copy2(source_path, target_path)

        artifact = {
            "artifact_id": str(uuid4()),
            "task_id": execution_context.task_id,
            "execution_id": execution_context.execution_id,
            "name": artifact_name,
            "path": str(target_path),
            "kind": kind,
            "created_at": utc_now(),
            "size_bytes": target_path.stat().st_size,
            "checksum_sha256": sha256_file(target_path),
        }
        artifacts = self._read_index(execution_context)
        artifacts.append(artifact)
        self._write_index(execution_context, artifacts)
        execution_context.log_context["artifact_index"] = str(self.index_path(execution_context))
        return artifact

    def register_text(self, content, execution_context, name, kind="text"):
        target_dir = self.execution_dir(execution_context)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / name
        target_path.write_text(content or "", encoding="utf-8")
        return self.register_file(target_path, execution_context, name=name, kind=kind)

    def _read_index(self, execution_context):
        index_path = self.index_path(execution_context)
        if not index_path.exists():
            return []
        return json.loads(index_path.read_text(encoding="utf-8"))

    def _write_index(self, execution_context, artifacts):
        index_path = self.index_path(execution_context)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps(artifacts, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

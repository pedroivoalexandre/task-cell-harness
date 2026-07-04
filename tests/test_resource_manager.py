import tempfile
import unittest
from pathlib import Path

from execution_context import ExecutionContext
from resource_manager import ResourceManager


class ResourceManagerTests(unittest.TestCase):
    def test_prepare_and_cleanup_execution_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            context = ExecutionContext.create({"id": "resource_task"})
            manager = ResourceManager(root / "runtime", project_root=root)
            workspace = manager.prepare_execution(context)
            self.assertTrue(workspace.exists())
            self.assertEqual(context.log_context["runtime_temp_dir"], str(workspace))
            (workspace / "file.txt").write_text("temp", encoding="utf-8")
            self.assertTrue(manager.cleanup_execution(context))
            self.assertFalse(workspace.exists())

    def test_cleanup_refuses_outside_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            context = ExecutionContext.create({"id": "resource_task"})
            context.log_context["runtime_temp_dir"] = str(root / "outside")
            manager = ResourceManager(root / "runtime", project_root=root)
            with self.assertRaises(ValueError):
                manager.cleanup_execution(context)


if __name__ == "__main__":
    unittest.main()

import unittest

from executors.mock import MockExecutor
from plugin_system import PluginRegistry


class PluginSystemTests(unittest.TestCase):
    def test_register_and_resolve_plugin(self):
        registry = PluginRegistry(allowed_plugins={"mock"})
        entry = registry.register("mock", MockExecutor(), plugin_type="executor")
        self.assertEqual(entry["name"], "mock")
        self.assertEqual(registry.resolve_by_name("mock"), entry)
        self.assertEqual(registry.resolve_by_type("executor"), [entry])

    def test_blocks_unallowed_plugin(self):
        registry = PluginRegistry(allowed_plugins={"safe"})
        with self.assertRaises(PermissionError):
            registry.register("unsafe", MockExecutor())

    def test_validates_interface(self):
        registry = PluginRegistry()
        with self.assertRaises(ValueError):
            registry.register("bad", object(), allowed=True)


if __name__ == "__main__":
    unittest.main()

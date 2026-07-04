class PluginRegistry:
    def __init__(self, allowed_plugins=None):
        self.allowed_plugins = set(allowed_plugins or [])
        self.plugins = {}

    def register(self, name, plugin, plugin_type="executor", allowed=False):
        if not allowed and self.allowed_plugins and name not in self.allowed_plugins:
            raise PermissionError(f"plugin not allowed: {name}")
        self.validate_interface(plugin)
        self.plugins[name] = {"name": name, "plugin": plugin, "type": plugin_type}
        return self.plugins[name]

    def validate_interface(self, plugin):
        for attr in ("name", "role", "execute"):
            if not hasattr(plugin, attr):
                raise ValueError(f"plugin missing required attribute: {attr}")
        if not callable(plugin.execute):
            raise ValueError("plugin execute must be callable")
        return True

    def resolve_by_name(self, name):
        return self.plugins.get(name)

    def resolve_by_type(self, plugin_type):
        return [entry for entry in self.plugins.values() if entry["type"] == plugin_type]

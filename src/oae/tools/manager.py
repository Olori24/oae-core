from .registry import TOOLS


class ToolManager:

    def list_tools(self):
        return list(TOOLS.keys())

    def get_tool(self, name):
        return TOOLS.get(name)

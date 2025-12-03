import importlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any

from langchain_core.tools import Tool

REGISTRY_PATH = Path(__file__).with_name("registry.yaml")
GENERATED_DIR = Path(__file__).with_name("generated")


class ToolMetadata(dict):
    """Thin wrapper just for type friendliness."""


class ToolRegistry:
    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.registry_path = registry_path
        self._tools_meta: Dict[str, ToolMetadata] = {}
        self._langchain_tools: Dict[str, Tool] = {}
        self._load_registry()
        self._load_langchain_tools()

    # ---------- loading ----------

    def _load_registry(self) -> None:
        if not self.registry_path.exists():
            # create empty registry file if missing
            self.registry_path.write_text("tools: {}\n")
        with open(self.registry_path, "r") as f:
            data = yaml.safe_load(f) or {}
        self._tools_meta = data.get("tools", {})

    def _save_registry(self) -> None:
        data = {"tools": self._tools_meta}
        with open(self.registry_path, "w") as f:
            yaml.safe_dump(data, f, sort_keys=True)

    def _load_langchain_tools(self) -> None:
        """Import all tools from metadata into LangChain Tool objects."""
        from langchain_core.tools import Tool

        for name, meta in self._tools_meta.items():
            module_path = meta["module"]
            func_name = meta["function"]
            description = meta.get("description", "")

            module = importlib.import_module(module_path)
            func = getattr(module, func_name)

            self._langchain_tools[name] = Tool(
                name=name,
                func=func,
                description=description,
            )

    # ---------- public API ----------

    @property
    def all_tool_names(self) -> List[str]:
        return list(self._tools_meta.keys())

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._langchain_tools.get(name)

    def get_tools_for_agent(self, agent_name: str) -> List[Tool]:
        """Return LangChain Tool objects that this agent is allowed to use."""
        tools = []
        for name, meta in self._tools_meta.items():
            allowed_agents = meta.get("agents", [])
            if agent_name in allowed_agents:
                tools.append(self._langchain_tools[name])
        return tools

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        return self._tools_meta.get(name)

    # ---------- dynamic registration / expansion ----------

    def register_existing_python_tool(
        self,
        name: str,
        module: str,
        function: str,
        description: str,
        agents: List[str],
        overwrite: bool = False,
    ) -> None:
        """
        Use this when you manually add a python file to the repo
        and want to register it in the YAML.
        """
        if name in self._tools_meta and not overwrite:
            raise ValueError(f"Tool '{name}' already exists. Use overwrite=True to replace.")

        self._tools_meta[name] = ToolMetadata(
            module=module,
            function=function,
            description=description,
            agents=agents,
        )
        # persist + hot-load
        self._save_registry()
        self._load_langchain_tools()

    def register_generated_tool(
        self,
        name: str,
        code: str,
        function: str,
        description: str,
        agents: List[str],
        subdir: str = "generated",
    ) -> None:
        """
        Use this when an LLM has generated new tool code.

        - Writes code into src/tools/<subdir>/<name>.py
        - Registers it in registry.yaml
        - Hot-loads it into the current process
        """
        GENERATED_DIR.mkdir(exist_ok=True)

        # 1. Write the new python file
        tool_file = GENERATED_DIR / f"{name}.py"
        if tool_file.exists():
            # simple strategy: append or overwrite; here we overwrite for clarity
            # you might want versioning instead.
            pass

        tool_file.write_text(code)

        # 2. Ensure generated package has __init__.py
        init_file = GENERATED_DIR / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# generated tools package\n")

        # 3. Module path relative to src (assuming src is on PYTHONPATH)
        module_path = f"tools.generated.{name}"

        # 4. Update metadata + save
        self._tools_meta[name] = ToolMetadata(
            module=module_path,
            function=function,
            description=description,
            agents=agents,
        )
        self._save_registry()

        # 5. Import + create LangChain Tool
        module = importlib.import_module(module_path)
        func = getattr(module, function)

        from langchain_core.tools import Tool
        self._langchain_tools[name] = Tool(
            name=name,
            func=func,
            description=description,
        )

    def build_structured_tools() -> Dict[str, Dict[str, Any]]:
        """
        Returns tools in the format expected by the hierarchical Agent:

        {
        "<tool_name>": {
            "definition": {  # for prompts
            "name": str,
            "description": str,
            "parameters": {"properties": {...}},
            "output_type": str,
            },
            "function": callable,  # actual Python function to execute
        },
        ...
        }
        """
        registry = ToolRegistry()
        structured: Dict[str, Dict[str, Any]] = {}

        for name, meta in registry._tools_meta.items():
            # load the underlying Python function
            module_path = meta["module"]
            func_name = meta["function"]

            module = importlib.import_module(module_path)
            func = getattr(module, func_name)

            # build the definition block with sensible defaults
            definition = {
                "name": name,
                "description": meta.get("description", ""),
                "parameters": meta.get("parameters", {"properties": {}}),
                "output_type": meta.get("output_type", "text"),
            }

            structured[name] = {
                "definition": definition,
                "function": func,
            }

        return structured
    
    tools: Dict[str, Dict[str, Any]] = build_structured_tools()
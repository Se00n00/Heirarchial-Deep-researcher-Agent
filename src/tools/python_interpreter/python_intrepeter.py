import asyncio
from types import ModuleType
from typing import Any
# from toolz import curry
from tools import AsyncTool, ToolResult
from local_python_executor import BASE_BUILTIN_MODULES, BASE_PYTHON_TOOLS, evaluate_python_code

# @TOOL.register_module(name="python_interpreter_tool", force=True)
class PythonInterpreterTool(AsyncTool):
    name = "python_interpreter_tool"
    description = "This is a tool that evaluates python code. It can be used to perform calculations."
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The python code to run in interpreter.",
            },
        },
        "required": ["code"],
    }
    output_type = "any"

    def __init__(self, *args, authorized_imports=None, **kwargs):
        if authorized_imports is None:
            self.authorized_imports = list(set(BASE_BUILTIN_MODULES))
        else:
            self.authorized_imports = list(set(BASE_BUILTIN_MODULES) | set(authorized_imports))
        self.parameters = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": (
                        "The code snippet to evaluate. All variables used in this snippet must be defined in this same snippet, "
                        f"else you will get an error. This code can only import the following python libraries: {self.authorized_imports}."
                    ),
                }
            },
            "required": ["code"],
        }
        self.base_python_tools = BASE_PYTHON_TOOLS
        self.python_evaluator = evaluate_python_code
        super().__init__(*args, **kwargs)

    async def forward(self, code: str) -> ToolResult:
        try:
            state = {}  # Initialize empty state
            try:
                eval_result = str(
                    self.python_evaluator(
                        code,
                        state=state,
                        static_tools=self.base_python_tools,
                        authorized_imports=self.authorized_imports,
                    )[0]  # The second element is boolean is_final_answer
                )
                
                # Get print outputs and convert to string if needed
                stdout = state.get('_print_outputs', '')
                if hasattr(stdout, '__str__'):
                    stdout = str(stdout)
                if stdout and not stdout.endswith('\n'):
                    stdout += '\n'
                
                stdout = stdout.rstrip() if stdout else ''
                output = f"Stdout:\n{stdout}\nOutput: {eval_result}"
                
                result = ToolResult(
                    output=output,
                    error=None
                )
            except Exception as inner_e:
                print(f"Inner exception: {str(inner_e)}")  # Debug information
                raise
        except Exception as e:
            result = ToolResult(
                output = None,
                error=str(e),
            )
        return result
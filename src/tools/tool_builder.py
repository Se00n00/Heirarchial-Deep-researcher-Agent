from langchain_openai import ChatOpenAI

tool_builder_llm = ChatOpenAI(model="gpt-4.1")

TOOL_BUILDER_SYSTEM_PROMPT = """
You are a senior Python engineer.
Given a description of a tool, you write a Python module that defines exactly one function.

Rules:
- The function name must be {function_name}.
- The function must be pure and synchronous.
- The function should have type hints.
- Do NOT include any imports that are not necessary.
- Do NOT use external APIs or packages that are not in the standard library, unless explicitly requested.
"""

def generate_tool_code(spec: str, function_name: str) -> str:
    prompt = TOOL_BUILDER_SYSTEM_PROMPT.format(function_name=function_name)
    user = f"Write the code for the tool.\n\nTool specification:\n{spec}"
    return tool_builder_llm.invoke([("system", prompt), ("user", user)]).content

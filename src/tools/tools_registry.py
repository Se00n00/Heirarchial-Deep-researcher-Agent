from tools.python_interpreter.python_intrepeter import PythonInterpreterTool
interpreter = PythonInterpreterTool()

tools = {
    "python_interpreter": {
        "name": "python_interpreter",
        "description": "Executes Python code and returns the output.",
        "parameters": {
            "properties": {
                "code": "Python code string to execute"
            }
        },
        "output_type": "execution_result",
        "function": interpreter.forward
    },

    "deep_analyzer_tool": {
        "name": "deep_analyzer_tool",
        "description": "A Groq-powered tool that performs systematic, step-by-step task analysis and reasoning, optionally using an attached file or URL for context.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "nullable": True,
                    "description": "The task to be analyzed. If omitted, the tool will caption or analyze the provided source."
                },
                "source": {
                    "type": "string",
                    "nullable": True,
                    "description": "Local file path or URL to analyze. Can handle PDF, text files, or external URIs."
                }
            },
            "required": []
        },
        "output_type": "any",
        "function": interpreter.forward
    },

    "python_interpreter_tool": {
        "name": "python_interpreter_tool",
        "description": "Evaluates Python code safely in a restricted interpreter environment.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Only imports from the allowed builtin list are permitted."
                }
            },
            "required": ["code"]
        },
        "output_type": "any",
        "function": interpreter.forward
    },

    "web_search": {
        "name": "web_search",
        "description": "Performs a Google-style web search and returns textual search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    },
                    "filter_year": {
                        "type": "string",
                        "nullable": True,
                        "description": "Optional. Restrict results to a specific year."
                    }
                },
                "required": ["query"]
            },
        "output_type": "string",
        "function": interpreter.forward
    }
}
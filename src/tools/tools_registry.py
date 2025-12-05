from tools.python_interpreter.python_intrepeter import PythonInterpreterTool
from tools.archive_searcher.archive_searcher import ArchiveSearcherTool

archive = ArchiveSearcherTool()
interpreter = PythonInterpreterTool()

tools = {
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
        "description": "Executes Python code safely in a restricted interpreter environment.",
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
    "archive_searcher_tool": {
        "name": "archive_searcher_tool",
        "description": "An async tool that searches the Wayback Machine for the closest archived snapshot of a URL before or at a given date, fetches the content, and returns a formatted summary including title and excerpt.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the webpage to find an archived version for."
                },
                "date": {
                    "type": "string",
                    "description": "The target date for the snapshot in YYYYMMDD format (e.g., '20231205'). The tool finds the closest available snapshot at or before this date."
                }
            },
            "required": ["url", "date"]
        },
        "output_type": "any",
        "function": archive.forward
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
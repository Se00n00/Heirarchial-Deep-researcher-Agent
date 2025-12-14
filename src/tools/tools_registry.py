from src.tools.python_interpreter.python_intrepeter import PythonInterpreterTool
from src.tools.archive_searcher.archive_searcher import ArchiveSearcherTool
from src.tools.web_browser.text_inspector import TextInspectorTool
from src.tools.web_browser.web_browser import (
    SearchInformationTool,
    DownloadTool,
    ArchiveSearchTool,
    FinderTool,
    FindNextTool,
    PageDownTool,
    PageUpTool,
    SimpleTextBrowser,
    VisitTool
)
import os
from dotenv import load_dotenv

load_dotenv()

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
BROWSER_CONFIG = {
    "viewport_size": 1024 * 5,
    "downloads_folder": "downloads_folder",
    "request_kwargs": {
        "headers": {"User-Agent": user_agent},
        "timeout": 300,
    },
    "serpapi_key": os.environ["SERPAPI_API_KEY"],
}
browser = SimpleTextBrowser(**BROWSER_CONFIG)

download_tool = DownloadTool(browser)
search_tool = SearchInformationTool(browser)
visit_tool = VisitTool(browser)
page_up_tool = PageUpTool(browser)
page_down_tool = PageDownTool(browser)
finder_tool = FinderTool(browser)
find_next_tool = FindNextTool(browser)
archive_search_tool = ArchiveSearchTool(browser)

archive = ArchiveSearcherTool()
interpreter = PythonInterpreterTool()

def final_answer(answer, citations = None):
    return answer

tools = {
    "final_answer":{
        "name":"final_answer",
        "description":"Use this submit your task",
        "parameters":{
            "type": "object",
            "properties": {
                "answer":{
                    "type":"string",
                    "description": "Exact result / feedback you want to give"
                },
                "citations":{
                    "type":"list[str]",
                    "description": "citations urls / source"
                }
            },
            "required": ["answer"]
        },
        "output_type":"any",
        "function": final_answer
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
        "function":  ""
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
    "web_search_tool":{
        "name": "web_search_tool",
        "description": "Perform a web search (using engines such as DuckDuckGo, Bing, Google, etc.) and return the results.",
        "parameters": {
            "type": "object",
            "properties": {
            "query": {
                "type": "string",
                "description": "The search query."
            },
            "filter_time": {
                "type": ["string", "null"],
                "description": "Optional time filter: d (day), w (week), m (month), y (year).",
                "default": None
            }
            },
            "required": ["query"]
        },
        "output_type": "string",
        "function": search_tool.forward
    },
    "download_tool":{
        "name": "download_tool",
        "description": """
Download a file from a URL. Allowed extensions: .xlsx, .pptx, .wav, .mp3, .m4a, .png, .jpg, .jpeg, .docx, etc.
Do NOT use for .pdf, .txt, .html — use visit_page instead.
ArXiv abstract URLs are automatically converted to PDF URLs.
        """.strip(),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Direct URL to the file."}
            },
            "required": ["url"]
        },
        "output_type": "string",
        "function": download_tool.forward
    },
    "visit_page": {
        "name": "visit_page",
        "description": "Visit a webpage at a given URL and return its text. for any given url it returns the markdown format of the webpage",
        "parameters": {
        "type": "object",
        "properties": {
            "url": {
            "type": "string",
            "description": "The relative or absolute url of the webpage to visit."
            }
        },
        "required": ["url"]
        },
        "output_type": "string",
        "function": visit_tool.forward
    },
    "page_up": {
        "name": "page_up",
        "description": "Scroll the viewport UP one page-length in the current webpage and return the new viewport content.",
        "parameters": {
        "type": "object",
        "properties": {},
        "required": []
        },
        "output_type": "string",
        "function": page_up_tool.forward
    },
    "page_down": {
        "name": "page_down",
        "description": "Scroll the viewport DOWN one page-length in the current webpage and return the new viewport content.",
        "parameters": {
        "type": "object",
        "properties": {},
        "required": []
        },
        "output_type": "string",
        "function": page_down_tool.forward
    },
    "find_on_page_ctrl_f": {
        "name": "find_on_page_ctrl_f",
        "description": "Scroll the viewport to the first occurrence of the search string. This is equivalent to Ctrl+F.",
        "parameters": {
        "type": "object",
        "properties": {
            "search_string": {
            "type": "string",
            "description": "The string to search for on the page. This search string supports wildcards like '*'"
            }
        },
        "required": ["search_string"]
        },
        "output_type": "string",
        "function": finder_tool.forward
    },
    "find_next": {
        "name": "find_next",
        "description": "Scroll the viewport to next occurrence of the search string. This is equivalent to finding the next match in a Ctrl+F search.",
        "parameters": {
        "type": "object",
        "properties": {},
        "required": []
        },
        "output_type": "string",
        "function": find_next_tool.forward
    },
    "find_archived_url": {
        "name": "find_archived_url",
        "description": "Given a url, searches the Wayback Machine and returns the archived version of the url that's closest in time to the desired date.",
        "parameters": {
        "type": "object",
        "properties": {
            "url": {
            "type": "string",
            "description": "The url you need the archive for."
            },
            "date": {
            "type": "string",
            "description": "The date that you want to find the archive for. Give this date in the format 'YYYYMMDD', for instance '27 June 2008' is written as '20080627'."
            }
        },
        "required": ["url", "date"]
        },
        "output_type": "string",
        "function": archive_search_tool.forward
    }
}
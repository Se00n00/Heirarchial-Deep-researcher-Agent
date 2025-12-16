from src.tools.python_interpreter.python_intrepeter import PythonInterpreterTool
from src.tools.archive_searcher.archive_searcher import ArchiveSearcherTool
from src.tools.web_browser.text_inspector import TextInspectorTool
from src.tools.final_answer import FinalAnswerTool
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
}

def tool_builder():
    # Instantiate all the class
    browser = SimpleTextBrowser(**BROWSER_CONFIG)
    
    download_tool = DownloadTool(browser)
    search_tool = SearchInformationTool(browser)
    visit_tool = VisitTool(browser)
    page_up_tool = PageUpTool(browser)
    page_down_tool = PageDownTool(browser)
    finder_tool = FinderTool(browser)
    find_next_tool = FindNextTool(browser)
    archive_search_tool = ArchiveSearchTool(browser)

    interpreter = PythonInterpreterTool()

    final_answer = FinalAnswerTool()

    tools = {}

    for object in [
        download_tool,
        search_tool,
        visit_tool,
        page_up_tool,
        page_down_tool,
        finder_tool,
        find_next_tool,
        archive_search_tool,
        interpreter,
        final_answer
        ]:
        tool_name = object.name
        tools[tool_name] = {
            "name": tool_name,
            "description": object.description,
            "parameters":{
                "type": "object",
                "properties": object.inputs,
                "required": [k for k, v in object.inputs.items() if not v.get("nullable", False)],
            },
            "output_type": object.output_type,
            "function": object.forward
        }

    return tools

# print(tool_builder())
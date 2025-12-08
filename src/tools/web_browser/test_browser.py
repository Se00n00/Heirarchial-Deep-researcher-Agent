from text_inspector import TextInspectorTool
from web_browser import (
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

download_tool = DownloadTool(browser)  #DONE
search_tool = SearchInformationTool(browser) #DONE

visit_tool = VisitTool(browser) # DONE
page_up_tool = PageUpTool(browser)
page_down_tool = PageDownTool(browser)
finder_tool = FinderTool(browser)
find_next_tool = FindNextTool(browser)
archive_search_tool = ArchiveSearchTool(browser)

print(search_tool.forward("japan"))
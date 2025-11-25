
import aiohttp
from waybackpy import WaybackMachineCDXServerAPI
from typing import Optional

class ToolResult:
    def __init__(self, output=None, error=None, title=None, markdown=None):
        self.output = output
        self.error = error
        self.title = title
        self.markdown = markdown

class DocumentConverterResult:
    def __init__(self, markdown: str, title: str):
        self.markdown = markdown
        self.title = title

class WebFetcherTool:
    async def forward(self, url: str) -> Optional[DocumentConverterResult]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    html = await resp.text()
                    # Attempt to extract <title>
                    start = html.find("<title>")
                    end = html.find("</title>", start)
                    if start != -1 and end != -1:
                        title = html[start+7:end]
                    else:
                        title = "No Title"
                    return DocumentConverterResult(markdown=html, title=title)
        except Exception as e:
            return DocumentConverterResult(markdown=f"Failed to fetch content: {e}", title="Error")

class ArchiveSearcherTool:
    def __init__(self):
        self.content_fetcher = WebFetcherTool()

    async def forward(self, url, date):
        try:
            # Use waybackpy to find the closest snapshot before or at the given date
            user_agent = "Mozilla/5.0 (compatible; WaybackBot/0.1)"
            cdx = WaybackMachineCDXServerAPI(url, user_agent)
            closest = cdx.near(date)
            archive_url = closest.archive_url
            timestamp = closest.timestamp if hasattr(closest, 'timestamp') else date
        except Exception as e:
            return ToolResult(output=None, error=f"No archive found for {url} on {date}: {e}")

        fetch_result = await self.content_fetcher.forward(archive_url)
        output = f"Web archive for url {url}, snapshot taken at {timestamp}:\n\n"
        output += f"Title: {fetch_result.title.strip() if fetch_result.title else 'NO Title'}\n\n"
        output += f"Content: {fetch_result.markdown.strip()[:500] if fetch_result.markdown else 'NO Content'}"
        return ToolResult(output=output, error=None)

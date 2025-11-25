import asyncio
from archive_searcher import ArchiveSearcherTool

tool = ArchiveSearcherTool()
url = "https://www.alltypehacks.net/"
date = "20240101"

async def test():
    result = await tool.forward(url, date)
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Success:\n{result.output}")

asyncio.run(test())

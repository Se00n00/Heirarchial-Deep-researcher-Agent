import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return


@app.cell
def _():
    import os
    import mimetypes
    import pathlib
    import re
    import time
    import uuid
    from typing import Any
    from urllib.parse import unquote, urljoin, urlparse
    import requests
    return


app._unparsable_cell(
    r"""
    class SimpleTextBrowser:
        \"\"\"(In preview) An extremely simple text-based web browser comparable to Lynx. Suitable for Agentic use.\"\"\"

        def __init__(
            self,
            start_page: str | None = None,
            viewport_size: int | None = 1024*8,  # Why ?
            downloads_folder: str | None | None = None,
            request_kwargs: dict[str, Any] | None | None = None
        ):
            self.start_page: str = start_page if start_page else \"about:blank\"
            self.viewport_size = viewport_size
            self.downloads_folder = downloads_folder
            self.history: list[tuple[str, float]] = list()
            self.page_title = str | None = None
            self.viewport_current_page = 0
            self.viewport_pages: list[tuple[int, int]] = list()
            self.set_address(self.start_page)
            self.request_kwargs = request_kwargs
            self.request_kwargs[\"cookies\"] = COOKIES # ???
            self._mdconvert = MarkdownConverter()
            self._page_content: str = \"\"
            self._find_on_page_query: str | None = None
            self._find_on_page_last_result: int | None = None

        @property
        def address(self) -> str:
            return self.history[-1][0]

        def set_address()
    """,
    name="_"
)


if __name__ == "__main__":
    app.run()

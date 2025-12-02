"""
deep_analyzer.py

Single-file Groq-powered Deep Analyzer tool.

Usage (from shell):

    export GROQ_API_KEY="your_key_here"
    python deep_analyzer.py

Or import in other code:

    from deep_analyzer import DeepAnalyzerTool
"""

import os
import asyncio
from dataclasses import dataclass
from pathlib import Path
from pypdf import PdfReader 
from typing import Optional, Dict, Any, List

from groq import Groq


# =========================
# Minimal tool abstractions
# =========================

@dataclass
class ToolResult:
    output: Optional[str]
    error: Optional[str] = None


class AsyncTool:
    """
    Minimal async tool base with a forward(...) method.
    """

    name: str = "async_tool"
    description: str = ""
    parameters: dict = {}
    output_type: str = "any"

    async def setup(self) -> None:
        """Optional one-time setup hook."""
        return None

    async def forward(self, *args, **kwargs) -> ToolResult:
        raise NotImplementedError

    async def __call__(self, *args, **kwargs) -> ToolResult:
        return await self.forward(*args, **kwargs)


# =====================
# Deep Analyzer Tool
# =====================

_DEEP_ANALYZER_DESCRIPTION = """A tool that performs systematic, step-by-step analysis or calculation of a given task, optionally leveraging information from external resources such as an attached file or URI to provide comprehensive reasoning and answers.
* At least one of `task` or `source` must be provided. When both are available, the tool will analyze and solve the task in the context of the provided source.
* The `source` can be a local file path or a URI.
"""

_DEEP_ANALYZER_INSTRUCTION = """You should step-by-step analyze the task and/or the attached content.
* When the task involves playing a game or performing calculations, consider the conditions imposed by the game or calculation rules. You may take extreme conditions into account.
* When the task involves spelling words, ensure that spelling rules are followed and the resulting word is meaningful.
* When the task involves computing the area of a specific polygon, separate the polygon into sub-polygons whose areas are easy to compute (rectangle, circle, triangle, etc.). Compute each area step-by-step and sum them.
* When the task involves calculation and statistics, consider all constraints. Failing to account for constraints can easily lead to statistical errors.

Here is the task:
"""

_DEEP_ANALYZER_SUMMARY_DESCRIPTION = """Please conduct a step-by-step analysis of the outputs from different models. Compare their results, identify discrepancies, extract the accurate components, eliminate the incorrect ones, and synthesize a coherent summary.
"""



class MarkitdownConverter:
    """
    Simple converter with basic file-type awareness.

    - If `source` is a .pdf file, extract its text using pypdf.
    - If it's any other existing file, read as UTF-8 text.
    - Otherwise, treat it as a raw reference (could be a URL, etc).

    NOTE: For very large files, we truncate to avoid sending huge prompts.
    """

    class _Result:
        def __init__(self, text_content: str):
            self.text_content = text_content

    def _read_pdf(self, path: Path) -> str:
        try:
            reader = PdfReader(str(path))
            chunks = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    chunks.append(f"--- Page {i + 1} ---\n{text}")
            if not chunks:
                return "[DeepAnalyzer] No extractable text found in this PDF."
            return "\n\n".join(chunks)
        except Exception as e:
            return f"[DeepAnalyzer] Failed to read PDF {path}: {e}"

    def _read_text_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return f"[DeepAnalyzer] Failed to read text file {path}: {e}"

    def convert(self, source: str) -> "_Result":
        p = Path(source)

        if p.exists() and p.is_file():
            ext = p.suffix.lower()
            if ext == ".pdf":
                text = self._read_pdf(p)
            else:
                text = self._read_text_file(p)

            # Optional: truncate to avoid mega-prompts
            max_chars = 15000
            if len(text) > max_chars:
                text = (
                    text[:max_chars]
                    + "\n\n[DeepAnalyzer] Content truncated for length. "
                      "Only the first part of the document is analyzed."
                )
        else:
            # Not a local file; could be URL or invalid path
            text = f"[DeepAnalyzer] Source is not a local file. Raw reference: {source}"

        return self._Result(text_content=text)


class DeepAnalyzerTool(AsyncTool):
    """
    Groq-powered Deep Analyzer.
    """

    name: str = "deep_analyzer_tool"
    description: str = _DEEP_ANALYZER_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "task": {
                "description": (
                    "The task to be analyzed and solved. If not provided, the tool "
                    "will focus solely on captioning/understanding the attached files or URLs."
                ),
                "type": "string",
                "nullable": True,
            },
            "source": {
                "description": (
                    "The attached file path or URI to be analyzed. The tool will "
                    "process and interpret the content of the file or webpage."
                ),
                "type": "string",
                "nullable": True,
            },
        },
        "required": [],
        "additionalProperties": False,
    }
    output_type = "any"

    def __init__(
        self,
        analyzer_model_ids: List[str],
        summarizer_model_id: str,
        groq_api_key: Optional[str] = None,
        groq_client: Optional[Groq] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ):
        """
        :param analyzer_model_ids: list of Groq chat model names used for analysis
        :param summarizer_model_id: Groq chat model name used to summarize analyses
        :param groq_api_key: optional; if omitted, uses $GROQ_API_KEY
        :param groq_client: optional pre-constructed Groq client
        """
        if not analyzer_model_ids:
            raise ValueError("at least one analyzer model id is required")

        self.analyzer_model_ids = analyzer_model_ids
        self.summarizer_model_id = summarizer_model_id

        api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        if groq_client is not None:
            self.client = groq_client
        else:
            if not api_key:
                raise ValueError(
                    "Groq API key not provided and GROQ_API_KEY env var is not set."
                )
            self.client = Groq(api_key=api_key)

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.converter: MarkitdownConverter = MarkitdownConverter()

    # ---------- internal helpers ----------

    async def _groq_chat(self, model: str, prompt: str) -> str:
        """
        Call Groq Chat Completions in a thread so we stay async-friendly.
        """
        from functools import partial

        def _call():
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return completion.choices[0].message.content

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _call)

    def _build_prompt(
        self,
        task: Optional[str],
        source: Optional[str],
    ) -> (str, bool):
        add_note = False
        if not task:
            add_note = True
            task = (
                "Please write a detailed caption/analysis for the attached file "
                "or URI and describe any important information it contains."
            )

        base = _DEEP_ANALYZER_INSTRUCTION + task

        if not source:
            return base, add_note

        ext = Path(source).suffix.lower()
        if ext in {".png", ".jpg", ".jpeg"}:
            context = (
                f"[NOTE] An image is available at path: {source}. "
                "You cannot see the image directly, but infer and describe what it might contain "
                "and perform the requested analysis accordingly."
            )
        else:
            try:
                extracted = self.converter.convert(source).text_content
            except Exception as e:
                extracted = f"Failed to extract content from {source}. Error: {e}"

            context = "Here is additional context from the attached source:\n\n" + extracted

        prompt = f"{base}\n\n{context}"
        return prompt, add_note

    async def _analyze(
        self,
        model_name: str,
        task: Optional[str],
        source: Optional[str],
    ) -> str:
        prompt, add_note = self._build_prompt(task, source)
        print(f"[DeepAnalyzer] Calling Groq model '{model_name}' for analysis...")
        output = await self._groq_chat(model_name, prompt)

        if add_note:
            output = (
                "You did not provide an explicit question, so here is a detailed "
                f"caption/analysis for the source:\n\n{output}"
            )
        return output

    async def _summarize(self, analyses: Dict[str, str]) -> str:
        prompt = _DEEP_ANALYZER_SUMMARY_DESCRIPTION + "\nAnalysis:\n"
        for model_name, text in analyses.items():
            prompt += f"--- {model_name} ---\n{text}\n\n"

        print(
            f"[DeepAnalyzer] Calling Groq model '{self.summarizer_model_id}' for summary..."
        )
        summary = await self._groq_chat(self.summarizer_model_id, prompt)
        return summary

    # ---------- public API ----------

    async def forward(
        self,
        task: Optional[str] = None,
        source: Optional[str] = None,
    ) -> ToolResult:
        """
        Run deep analysis across multiple Groq models and summarize their outputs.
        """
        if not task and not source:
            return ToolResult(
                output=None,
                error="At least one of `task` or `source` must be provided.",
            )

        analyses: Dict[str, str] = {}

        for model_name in self.analyzer_model_ids:
            try:
                analysis = await self._analyze(model_name, task, source)
                analyses[model_name] = analysis
                print(
                    f"[DeepAnalyzer] Got analysis from '{model_name}' "
                    f"(first 300 chars):\n{analysis[:300]}...\n"
                )
            except Exception as e:
                err_msg = f"[ERROR calling {model_name} via Groq]: {e}"
                print(err_msg)
                analyses[model_name] = err_msg

        try:
            summary = await self._summarize(analyses)
        except Exception as e:
            return ToolResult(
                output=None,
                error=f"Failed to summarize analyses via Groq: {e}",
            )

        parts: List[str] = ["Analysis of models:"]
        for model_name, text in analyses.items():
            parts.append(f"\n### {model_name}\n{text}\n")
        parts.append("\n### Summary\n")
        parts.append(summary)

        return ToolResult(output="\n".join(parts), error=None)


# =======================
# Quick test / demo block
# =======================

async def _demo():
    """
    Simple demo: run this file directly to test the tool.
    Adjust `task` and `source` as you like.
    """
    # 1. Choose models
    analyzer_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]
    summarizer_model = "llama-3.3-70b-versatile"

    # 2. Make tool
    tool = DeepAnalyzerTool(
        analyzer_model_ids=analyzer_models,
        summarizer_model_id=summarizer_model,
        # groq_api_key="...",  # optional if GROQ_API_KEY env is set
    )

    # 3. Define a task + (optional) source file
    task = "You are a senior engineer. Analyze this task and produce a step-by-step reasoning and final answer: Explain what a multi-agent research system is and list key design considerations."
    # If you have a local file, put its path here; otherwise None
    source = None  # e.g. "docs/research_notes.txt"

    print("[DeepAnalyzer] Running demo...\n")
    result = await tool.forward(task=task, source=source)

    if result.error:
        print("ERROR:", result.error)
    else:
        print("\n================ FINAL OUTPUT ================\n")
        print(result.output)


async def _demo2():
    analyzer_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]
    summarizer_model = "llama-3.3-70b-versatile"

    tool = DeepAnalyzerTool(
        analyzer_model_ids=analyzer_models,
        summarizer_model_id=summarizer_model,
    )

    task = "Read this document and give me a concise summary of what this document is all about"
    source = "samples/sample.pdf"  # put a real PDF path here

    print("[DeepAnalyzer] Running PDF demo...\n")
    result = await tool.forward(task=task, source=source)

    if result.error:
        print("ERROR:", result.error)
    else:
        print("\n================ FINAL OUTPUT ================\n")
        print(result.output)


from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    # Run demo when executed as a script
    if not os.environ.get("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY environment variable is not set.")
        print("Set it before running, e.g.: export GROQ_API_KEY='your_key_here'\n")

    asyncio.run(_demo2())

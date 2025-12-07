import json
import re
from typing import List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field, model_validator

from tools import AsyncTool, ToolResult
from web_searcher import WebSearcherTool
from models import ChatMessage, model_manager


def _extract_json_from_text(text: str) -> str:
    """Extract JSON object from model reply that may contain markdown fences."""
    if not text:
        raise ValueError("Empty text")
    
    s = text.strip()
    
    # Remove markdown code fences
    m = re.search(r"``````", s, flags=re.DOTALL)
    if m:
        return m.group(1)
    
    # Extract first {...} object
    start = s.find('{')
    end = s.rfind('}')
    if start != -1 and end != -1 and end > start:
        return s[start:end+1]
    
    raise ValueError("No JSON object found in model output")


class ResearchInsight(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    content: str = Field(description="The insight content")
    source_url: str = Field(description="URL where this insight was found")
    source_title: Optional[str] = Field(default=None, description="Title of the source")
    relevance_score: float = Field(default=1.0, description="Relevance score (0.0-1.0)", ge=0.0, le=1.0)
    
    def __str__(self):
        source = self.source_title or self.source_url
        return f"{self.content} [Source: {source}]"


class ResearchContext(BaseModel):
    query: str = Field(description="The original research query")
    insights: List[ResearchInsight] = Field(default_factory=list)
    follow_up_queries: List[str] = Field(default_factory=list)
    visited_urls: Set[str] = Field(default_factory=set)
    current_depth: int = Field(default=0)
    max_depth: int = Field(default=2)


class ResearchSummary(BaseModel):
    output: str = Field(default="")
    query: str = Field(description="The original research query")
    insights: List[ResearchInsight] = Field(default_factory=list)
    visited_urls: Set[str] = Field(default_factory=set)
    depth_reached: int = Field(default=0)
    
    @model_validator(mode="after")
    def populate_output(self):
        grouped_insights = {
            "Key Findings": [i for i in self.insights if i.relevance_score >= 0.8],
            "Additional Information": [i for i in self.insights if 0.5 <= i.relevance_score < 0.8],
            "Supplementary Information": [i for i in self.insights if i.relevance_score < 0.5],
        }
        
        sections = [
            f"# Research: {self.query}\n",
            f"**Sources**: {len(self.visited_urls)} | **Depth**: {self.depth_reached + 1}\n",
        ]
        
        for section_title, insights in grouped_insights.items():
            if insights:
                sections.append(f"## {section_title}")
                for insight in insights:
                    sections.extend([
                        insight.content,
                        f"> Source: [{insight.source_title or 'Link'}]({insight.source_url})\n"
                    ])
        
        self.output = "\n".join(sections)
        return self


# Prompts
OPTIMIZE_QUERY_INSTRUCTION = """You are a research assistant helping to optimize a search query for web research.
Your task is to reformulate the given query to be more effective for web searches.
Make it specific, use relevant keywords, and ensure it's clear and concise.

Original query: {query}

Provide the optimized query text without any explanation or additional formatting."""

EXTRACT_INSIGHTS_PROMPT = """Analyze the following content and extract key insights related to the research query.
For each insight, assess its relevance to the query on a scale of 0.0 to 1.0.

Research query: {query}
Content to analyze:
{content}

Extract up to 3 most important insights from this content. For each insight:
1. Provide the insight content
2. Provide relevance score (0.0-1.0)"""

GENERATE_FOLLOW_UPS_PROMPT = """Based on the insights discovered so far, generate follow-up research queries to explore gaps or related areas.
These should help deepen our understanding of the topic.

Original query: {original_query}
Current query: {current_query}
Key insights so far:
{insights}

Generate up to 3 specific follow-up queries that would help address gaps in our current knowledge.
Each query should be concise and focused on a specific aspect of the research topic."""


class DeepResearcherTool(AsyncTool):
    name = "deep_researcher_tool"
    description = "Performs comprehensive research on a topic through multi-level web searches and content analysis."
    
    def __init__(self, model_id='gpt-4.1', max_depth=2, max_insights=20, time_limit_seconds=120, max_follow_ups=3):
        super().__init__()
        self.model_id = model_id
        self.max_depth = max_depth
        self.max_insights = max_insights
        self.time_limit_seconds = time_limit_seconds
        self.max_follow_ups = max_follow_ups
        
        model = model_manager.registered_models.get(self.model_id)
        if model is None:
            raise RuntimeError(
                f"Model '{self.model_id}' is not registered in model_manager.registered_models. "
                f"Available models: {list(model_manager.registered_models.keys())}"
            )
        self.model = model
        self.web_searcher = WebSearcherTool()
        self.web_searcher.fetch_content = True
    
    async def forward(self, query: str):
        import time
        
        max_depth = max(1, min(self.max_depth, 5))
        context = ResearchContext(query=query, max_depth=max_depth)
        deadline = time.time() + self.time_limit_seconds
        
        try:
            optimized_query, filter_year = await self._generate_optimized_query(query)
            await self._research_graph(context, optimized_query, filter_year, deadline)
        except Exception as e:
            return ToolResult(output=None, error=str(e))
        
        reference = ResearchSummary(
            query=query,
            insights=sorted(context.insights, key=lambda x: x.relevance_score, reverse=True)[:self.max_insights],
            visited_urls=context.visited_urls,
            depth_reached=context.current_depth,
        )
        
        output = await self._summary(query, reference.output)
        return ToolResult(output=output, error=None)
    
    async def _generate_optimized_query(self, query):
        prompt = OPTIMIZE_QUERY_INSTRUCTION.format(query=query)
        messages = [ChatMessage(role='user', content=prompt)]
        
        response = await self.model(messages)
        content = getattr(response, 'content', None) or str(response)
        
        # Simple parsing - extract optimized query from response
        optimized_query = content.strip() if content else query
        return optimized_query, None
    
    async def _research_graph(self, context, query, filter_year=None, deadline=None):
        import time
        
        if time.time() >= deadline or context.current_depth >= context.max_depth:
            return
        
        search_results = await self._search_web(query, filter_year)
        if not search_results:
            return
        
        new_insights = await self._extract_insights(context, search_results, context.query, deadline)
        if not new_insights:
            return
        
        follow_ups = await self._generate_follow_ups(new_insights, query, context.query)
        context.follow_up_queries.extend(follow_ups)
        context.current_depth += 1
        
        if follow_ups and context.current_depth < context.max_depth:
            for follow_up in follow_ups[:2]:
                if time.time() >= deadline:
                    break
                await self._research_graph(context, follow_up, filter_year, deadline)
    
    async def _search_web(self, query, filter_year=None):
        search_response = await self.web_searcher.forward(query=query, filter_year=filter_year)
        return [] if getattr(search_response, 'error', False) else getattr(search_response, 'results', [])
    
    async def _extract_insights(self, context, results, original_query, deadline):
        import time
        
        all_insights = []
        for rst in results:
            if rst.url in context.visited_urls or time.time() >= deadline:
                continue
            
            context.visited_urls.add(rst.url)
            if not rst.raw_content:
                continue
            
            insights = await self._analyze_content(rst.raw_content, rst.url, rst.title, original_query)
            all_insights.extend(insights)
            context.insights.extend(insights)
        
        return all_insights
    
    async def _generate_follow_ups(self, insights, current_query, original_query):
        if not insights:
            return []
        
        insights_txt = "\n".join([f"- {i.content}" for i in insights[:5]])
        prompt = GENERATE_FOLLOW_UPS_PROMPT.format(
            original_query=original_query,
            current_query=current_query,
            insights=insights_txt
        )
        
        messages = [ChatMessage(role='user', content=prompt)]
        response = await self.model(messages)
        
        content = getattr(response, 'content', '') or str(response)
        
        # Simple parsing - extract queries from numbered or bulleted list
        queries = []
        for line in content.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # Remove numbering/bullets
                clean_line = re.sub(r'^[\d\.\-\*\)\s]+', '', line).strip()
                if clean_line:
                    queries.append(clean_line)
        
        return queries[:self.max_follow_ups]
    
    async def _analyze_content(self, content, url, title, query):
        prompt = EXTRACT_INSIGHTS_PROMPT.format(query=query, content=content[:2000])
        messages = [ChatMessage(role='user', content=prompt)]
        
        response = await self.model(messages)
        content_text = getattr(response, 'content', '') or str(response)
        
        insights = []
        try:
            json_text = _extract_json_from_text(content_text)
            parsed = json.loads(json_text)
            
            extracted = parsed.get("insights", [])
            for data in extracted:
                insights.append(ResearchInsight(
                    content=data.get("content", ""),
                    source_url=url,
                    source_title=title,
                    relevance_score=data.get("relevance_score", 0.7)
                ))
        except Exception:
            # Fallback: create single insight from first part of content
            insights.append(ResearchInsight(
                content=f"Content from {title or url}"[:500],
                source_url=url,
                source_title=title,
                relevance_score=0.5,
            ))
        
        return insights
    
    async def _summary(self, query, reference_materials):
        model = model_manager.registered_models.get('gpt-4o-search-preview') or self.model
        messages = [ChatMessage(role='user', content=query)]
        response = await model(messages)
        content = getattr(response, 'content', '(summary)')
        return reference_materials + "\n" + content


if __name__ == "__main__":
    import asyncio
    
    async def test():
        tool = DeepResearcherTool()
        query = "How to make the best cheese omelette?"
        result = await tool.forward(query=query)
        
        if result.error:
            print(f"Error: {result.error}")
        else:
            print(f"Success:\n{result.output}")
    
    asyncio.run(test())

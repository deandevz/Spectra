import os

from langchain_tavily import TavilySearch

from display import display_search_done, display_search_progress, display_step
from models_config import get_llm
from prompts import load_prompt
from state import ResearchState, SearchResult, Source


def _extract_relevant_content(llm, raw_content: str, topic: str, title: str) -> str:
    """Extract the most relevant 500-800 tokens from raw page content."""
    if not raw_content or len(raw_content) < 200:
        return raw_content or ""

    # Truncate very long pages to avoid exceeding context limits
    truncated = raw_content[:15000]

    response = llm.invoke([
        {
            "role": "system",
            "content": "You are a content extractor. Extract the most relevant information from the given web page content that relates to the research topic. Return only the extracted content — no commentary. Focus on facts, data, statistics, names, dates, and concrete evidence. Write 500-800 words.",
        },
        {
            "role": "user",
            "content": f"Research topic: {topic}\nSource: {title}\n\nPage content:\n{truncated}",
        },
    ])
    return response.content


def researcher_node(state: ResearchState) -> dict:
    display_step("RESEARCHER", "Searching and summarizing sources")

    subtopics = state["subtopics"]
    llm = get_llm("researcher")
    tavily = TavilySearch(max_results=5, include_raw_content="markdown")

    all_results: list[dict] = state.get("search_results", [])
    all_sources: list[dict] = state.get("sources", [])

    for i, topic in enumerate(subtopics, 1):
        display_search_progress(topic, i, len(subtopics))

        # Search with Tavily
        raw_response = tavily.invoke(topic)
        raw_results = raw_response.get("results", []) if isinstance(raw_response, dict) else []

        # Extract sources and content
        topic_sources = []
        search_content_parts = []
        for r in raw_results:
            url = r.get("url", "")
            title = r.get("title", url)
            raw_content = r.get("raw_content", "")
            content = r.get("content", "")
            if url:
                source = Source(url=url, title=title, used_in=topic)
                topic_sources.append(source.model_dump())
                all_sources.append(source.model_dump())

            # Use raw_content (full page) when available, fall back to snippet
            if raw_content:
                extracted = _extract_relevant_content(llm, raw_content, topic, title)
                search_content_parts.append(f"[{title}] ({url}):\n{extracted}")
            elif content:
                search_content_parts.append(f"[{title}] ({url}):\n{content}")

        search_content = "\n\n---\n\n".join(search_content_parts)

        # Summarize with LLM
        system_msg, user_msg = load_prompt(
            "researcher",
            query=topic,
            search_content=search_content,
        )

        response = llm.invoke([
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ])

        result = SearchResult(
            query=topic,
            sources=topic_sources,
            summary=response.content,
        )
        all_results.append(result.model_dump())

    display_search_done(len(all_sources))

    # Build organized context by subtopic (no lossy compression)
    compressed_context = "\n\n".join(
        f"## {r['query']}\n{r['summary']}" for r in all_results
    )

    return {
        "search_results": all_results,
        "compressed_context": compressed_context,
        "sources": all_sources,
    }

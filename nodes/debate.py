import json
import re

from langchain_tavily import TavilySearch

from display import display_debate_argument, display_debater_search, display_step
from models_config import get_llm
from prompts import load_prompt
from state import Argument, DebateRound, Evidence, ResearchState, Source

MAX_DEBATE_ROUNDS = 2


def _parse_structured_argument(response_text: str, agent: str, role: str, round_num: int) -> Argument:
    """Parse structured JSON from debater response, with fallback to plain text."""
    try:
        cleaned = re.sub(r"```(?:json)?\s*", "", response_text)
        cleaned = cleaned.strip().rstrip("`")
        data = json.loads(cleaned)

        main_arg = data.get("main_argument", "")
        evidence_list = [
            Evidence(claim=e["claim"], source=e.get("source", ""))
            for e in data.get("evidence", [])
        ]
        rebuttal_to = data.get("rebuttal_to", "")
        confidence = float(data.get("confidence", 0.0))
        unresolved = data.get("unresolved_questions", [])

        # Build readable text from structured data
        text_parts = [main_arg]
        if evidence_list:
            text_parts.append("\n\nEvidence:")
            for e in evidence_list:
                text_parts.append(f"- {e.claim} (Fonte: {e.source})")
        if unresolved:
            text_parts.append("\n\nOpen questions:")
            for q in unresolved:
                text_parts.append(f"- {q}")

        return Argument(
            agent=agent,
            role=role,
            text="\n".join(text_parts),
            main_argument=main_arg,
            evidence=evidence_list,
            rebuttal_to=rebuttal_to,
            confidence=confidence,
            unresolved_questions=unresolved,
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        # Fallback: treat as plain text
        return Argument(
            agent=agent,
            role=role,
            text=response_text,
            main_argument=response_text,
        )


def _generate_search_query(llm, perspective: dict, prev_args: str, query: str) -> str:
    """Generate a targeted search query for the debater to find counter-evidence."""
    response = llm.invoke([
        {
            "role": "system",
            "content": "You are a debate research assistant. Generate a single, specific web search query to find evidence that supports the debater's rebuttal. Return ONLY the search query text, nothing else.",
        },
        {
            "role": "user",
            "content": f"Debate topic: {query}\nDebater perspective: {perspective['system_prompt']}\n\nArguments to rebut:\n{prev_args}\n\nGenerate one specific search query to find evidence for the rebuttal:",
        },
    ])
    return response.content.strip().strip('"')


def _search_and_extract(llm, search_query: str, topic: str) -> tuple[str, list[dict]]:
    """Search Tavily and extract relevant evidence."""
    tavily = TavilySearch(max_results=3, include_raw_content="markdown")
    raw_response = tavily.invoke(search_query)
    raw_results = raw_response.get("results", []) if isinstance(raw_response, dict) else []

    new_sources = []
    evidence_parts = []

    for r in raw_results:
        url = r.get("url", "")
        title = r.get("title", url)
        raw_content = r.get("raw_content", "")
        content = r.get("content", "")

        if url:
            new_sources.append(Source(url=url, title=title, used_in=f"debate:{topic}").model_dump())

        page_content = raw_content or content
        if page_content:
            # Extract relevant portion via LLM
            truncated = page_content[:10000]
            extract_response = llm.invoke([
                {
                    "role": "system",
                    "content": "Extract the most relevant evidence from this page for the debate topic. Return only the key facts, data, and arguments in 200-300 words. No commentary.",
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}\nSearch query: {search_query}\n\nPage [{title}]:\n{truncated}",
                },
            ])
            evidence_parts.append(f"[{title}] ({url}):\n{extract_response.content}")

    evidence_text = "\n\n".join(evidence_parts) if evidence_parts else ""
    return evidence_text, new_sources


def debate_node(state: ResearchState) -> dict:
    current_round = state.get("current_round", 0)
    round_num = current_round + 1
    display_step(f"DEBATE — Rodada {round_num}", "Debate roundtable")

    perspectives = state["perspectives"]
    compressed_context = state["compressed_context"]
    debate_rounds = list(state.get("debate_rounds", []))
    all_sources = list(state.get("sources", []))

    arguments = []

    for idx, perspective in enumerate(perspectives):
        debater_key = f"debater_{idx + 1}"
        llm = get_llm(debater_key)

        if round_num == 1:
            system_msg, user_msg = load_prompt(
                "debate_round1",
                query=state["query"],
                compressed_context=compressed_context,
                perspective_prompt=perspective["system_prompt"],
            )
        else:
            # Format previous arguments for context
            prev_args = _format_previous_arguments(debate_rounds, perspective["name"])

            # Search for additional evidence to support rebuttal
            search_query = _generate_search_query(llm, perspective, prev_args, state["query"])
            display_debater_search(perspective["name"], search_query)

            evidence_text, new_sources = _search_and_extract(llm, search_query, state["query"])
            all_sources.extend(new_sources)

            additional_evidence_section = ""
            if evidence_text:
                additional_evidence_section = f"Additional evidence found for your rebuttal:\n{evidence_text}"

            system_msg, user_msg = load_prompt(
                "debate_round2",
                query=state["query"],
                compressed_context=compressed_context,
                perspective_prompt=perspective["system_prompt"],
                previous_arguments=prev_args,
                additional_evidence=additional_evidence_section,
            )

        response = llm.invoke([
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ])

        argument = _parse_structured_argument(
            response.content, perspective["name"], perspective["role"], round_num
        )
        arguments.append(argument.model_dump())

        display_debate_argument(
            perspective["name"],
            perspective["role"],
            argument.text,
            round_num,
        )

    debate_round = DebateRound(
        round_num=round_num,
        arguments=arguments,
    )
    debate_rounds.append(debate_round.model_dump())

    return {
        "debate_rounds": debate_rounds,
        "current_round": round_num,
        "sources": all_sources,
    }


def should_continue_debate(state: ResearchState) -> str:
    if state.get("current_round", 0) < MAX_DEBATE_ROUNDS:
        return "debate"
    return "moderator"


def _format_previous_arguments(debate_rounds: list[dict], exclude_name: str) -> str:
    parts = []
    for dr in debate_rounds:
        for arg in dr["arguments"]:
            if arg["agent"] != exclude_name:
                parts.append(f"**{arg['agent']}** ({arg['role']}):\n{arg['text']}")
    return "\n\n---\n\n".join(parts)

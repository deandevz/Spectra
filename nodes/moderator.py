import json
import re

from display import display_more_research, display_step, display_synthesis
from models_config import get_llm
from prompts import load_prompt
from state import ResearchState, Synthesis


def moderator_node(state: ResearchState) -> dict:
    display_step("MODERADOR", "Synthesizing the debate")

    llm = get_llm("moderator")

    debate_transcript = _format_debate_transcript(state.get("debate_rounds", []))

    system_msg, user_msg = load_prompt(
        "moderator",
        query=state["query"],
        compressed_context=state["compressed_context"],
        debate_transcript=debate_transcript,
    )

    response = llm.invoke([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ])

    parsed = _parse_json(response.content)
    synthesis = Synthesis(**parsed)
    synthesis_dict = synthesis.model_dump()

    display_synthesis(synthesis_dict)

    research_loop_count = state.get("research_loop_count", 0)
    needs_more = bool(synthesis.gap_queries) and research_loop_count < 1

    result = {
        "synthesis": synthesis_dict,
        "needs_more_research": needs_more,
        "research_loop_count": research_loop_count + (1 if needs_more else 0),
    }

    if needs_more:
        display_more_research(synthesis.gap_queries)
        result["subtopics"] = synthesis.gap_queries

    return result


def should_research_more(state: ResearchState) -> str:
    if state.get("needs_more_research", False):
        return "researcher"
    return "publisher"


def _format_debate_transcript(debate_rounds: list[dict]) -> str:
    parts = []
    for dr in debate_rounds:
        parts.append(f"### Round {dr['round_num']}")
        for arg in dr["arguments"]:
            header = f"\n**{arg['agent']}** ({arg['role']})"
            if arg.get("confidence"):
                header += f" [confidence: {arg['confidence']:.1f}]"
            parts.append(f"{header}:\n{arg['text']}")
            # Include structured evidence if available
            evidence = arg.get("evidence", [])
            if evidence:
                parts.append("\nStructured evidence:")
                for e in evidence:
                    parts.append(f"  - {e['claim']} (Fonte: {e['source']})")
            unresolved = arg.get("unresolved_questions", [])
            if unresolved:
                parts.append("\nOpen questions:")
                for q in unresolved:
                    parts.append(f"  - {q}")
    return "\n\n".join(parts)


def _parse_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.strip().rstrip("`")
    return json.loads(cleaned)

from pathlib import Path

from display import display_final_report_saved, display_step
from models_config import get_llm
from prompts import load_prompt
from state import ResearchState

OUTPUT_FILE = "final_result.txt"


def publisher_node(state: ResearchState) -> dict:
    display_step("PUBLISHER", "Generating final report")

    llm = get_llm("publisher")

    debate_transcript = _format_debate_transcript(state.get("debate_rounds", []))
    synthesis_text = _format_synthesis(state.get("synthesis", {}))
    sources_text = _format_sources(state.get("sources", []))

    # Build evaluation feedback if available (from Evaluator rerun)
    eval_feedback = state.get("evaluation_feedback", "")
    if eval_feedback:
        eval_section = f"IMPORTANT — Previous evaluation feedback (improve these areas):\n{eval_feedback}"
    else:
        eval_section = ""

    system_msg, user_msg = load_prompt(
        "publisher",
        query=state["query"],
        synthesis=synthesis_text,
        debate_transcript=debate_transcript,
        sources=sources_text,
        evaluation_feedback=eval_section,
    )

    response = llm.invoke([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ])

    report = response.content
    output_path = Path(__file__).parent.parent / OUTPUT_FILE
    output_path.write_text(report, encoding="utf-8")

    display_final_report_saved(str(output_path))

    return {"final_report": report}


def _format_debate_transcript(debate_rounds: list[dict]) -> str:
    parts = []
    for dr in debate_rounds:
        parts.append(f"### Round {dr['round_num']}")
        for arg in dr["arguments"]:
            header = f"\n**{arg['agent']}** ({arg['role']})"
            if arg.get("confidence"):
                header += f" [confidence: {arg['confidence']:.1f}]"
            parts.append(f"{header}:\n{arg['text']}")
            # Include structured evidence for citation generation
            evidence = arg.get("evidence", [])
            if evidence:
                parts.append("\nCitable evidence:")
                for e in evidence:
                    parts.append(f"  - \"{e['claim']}\" — Fonte: {e['source']}")
    return "\n\n".join(parts)


def _format_synthesis(synthesis: dict) -> str:
    parts = []
    if synthesis.get("consensus"):
        parts.append("**Consensos:**")
        for item in synthesis["consensus"]:
            parts.append(f"- {item}")
    if synthesis.get("conflicts"):
        parts.append("\n**Conflitos:**")
        for item in synthesis["conflicts"]:
            parts.append(f"- {item}")
    if synthesis.get("gaps"):
        parts.append("\n**Lacunas:**")
        for item in synthesis["gaps"]:
            parts.append(f"- {item}")
    return "\n".join(parts)


def _format_sources(sources: list[dict]) -> str:
    seen = set()
    parts = []
    for s in sources:
        url = s.get("url", "")
        if url and url not in seen:
            seen.add(url)
            title = s.get("title", url)
            parts.append(f"- [{title}]({url})")
    return "\n".join(parts)

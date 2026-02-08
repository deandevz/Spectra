import json
import re

from display import display_evaluation, display_step
from models_config import get_llm
from prompts import load_prompt
from state import ResearchState


def evaluator_node(state: ResearchState) -> dict:
    display_step("EVALUATOR", "Evaluating report quality")

    llm = get_llm("evaluator")
    report = state.get("final_report", "")

    system_msg, user_msg = load_prompt(
        "evaluator",
        query=state["query"],
        report=report,
    )

    response = llm.invoke([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ])

    parsed = _parse_json(response.content)

    scores = parsed.get("scores", {})
    average = parsed.get("average", 0.0)
    feedback = parsed.get("feedback", "")
    justifications = parsed.get("justifications", {})

    evaluation = {
        "scores": scores,
        "average": average,
        "justifications": justifications,
    }

    display_evaluation(evaluation)

    loop_count = state.get("evaluation_loop_count", 0)

    result: dict = {
        "evaluation": evaluation,
        "evaluation_loop_count": loop_count + 1,
    }

    # If quality is insufficient and we haven't retried yet, send feedback to publisher
    if average < 7.0 and loop_count < 1 and feedback:
        result["evaluation_feedback"] = feedback
    else:
        result["evaluation_feedback"] = ""

    return result


def should_rerun_publisher(state: ResearchState) -> str:
    feedback = state.get("evaluation_feedback", "")
    if feedback:
        return "publisher"
    return "end"


def _parse_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.strip().rstrip("`")
    return json.loads(cleaned)

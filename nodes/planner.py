import json
import re

from display import display_perspectives, display_step, display_subtopics
from models_config import get_llm
from prompts import load_prompt
from state import Perspective, ResearchState


def planner_node(state: ResearchState) -> dict:
    display_step("PLANNER", "Decomposing query into subtopics and perspectives")

    llm = get_llm("planner")
    system_msg, user_msg = load_prompt("planner", query=state["query"])

    response = llm.invoke([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ])

    parsed = _parse_json(response.content)

    subtopics = parsed["subtopics"]
    perspectives = []
    for p in parsed["perspectives"]:
        perspective = Perspective(**p)
        perspectives.append(perspective.model_dump())

    display_subtopics(subtopics)
    display_perspectives(perspectives)

    return {
        "subtopics": subtopics,
        "perspectives": perspectives,
    }


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response, stripping markdown code fences if present."""
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.strip().rstrip("`")
    return json.loads(cleaned)

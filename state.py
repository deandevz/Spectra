from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel


# ── Pydantic Models ──


class Perspective(BaseModel):
    name: str
    role: str  # advocate, critic, analyst
    system_prompt: str


class Source(BaseModel):
    url: str
    title: str
    used_in: str  # which subtopic


class SearchResult(BaseModel):
    query: str
    sources: list[Source]
    summary: str


class Evidence(BaseModel):
    claim: str
    source: str  # source title


class Argument(BaseModel):
    agent: str
    role: str
    text: str
    main_argument: str = ""
    evidence: list[Evidence] = []
    rebuttal_to: str = ""  # only in round 2
    confidence: float = 0.0
    unresolved_questions: list[str] = []


class DebateRound(BaseModel):
    round_num: int
    arguments: list[Argument]


class Synthesis(BaseModel):
    consensus: list[str]
    conflicts: list[str]
    gaps: list[str]
    gap_queries: list[str]


# ── LangGraph State ──


class ResearchState(TypedDict, total=False):
    # Input
    query: str

    # Planner
    subtopics: list[str]
    perspectives: list[dict]  # Perspective dicts (JSON-serializable)

    # Researcher
    search_results: list[dict]  # SearchResult dicts
    compressed_context: str
    sources: list[dict]  # Source dicts

    # Debate
    debate_rounds: list[dict]  # DebateRound dicts
    current_round: int

    # Moderator
    synthesis: dict  # Synthesis dict
    needs_more_research: bool
    research_loop_count: int

    # Publisher
    final_report: str

    # Evaluator
    evaluation: dict
    evaluation_feedback: str
    evaluation_loop_count: int

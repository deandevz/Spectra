from langgraph.graph import END, StateGraph

from nodes.debate import debate_node, should_continue_debate
from nodes.evaluator import evaluator_node, should_rerun_publisher
from nodes.moderator import moderator_node, should_research_more
from nodes.planner import planner_node
from nodes.publisher import publisher_node
from nodes.researcher import researcher_node
from state import ResearchState


def build_graph():
    graph = StateGraph(ResearchState)

    # Nodes
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("debate", debate_node)
    graph.add_node("moderator", moderator_node)
    graph.add_node("publisher", publisher_node)
    graph.add_node("evaluator", evaluator_node)

    # Flow
    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "debate")

    # Debate loop (2 rounds)
    graph.add_conditional_edges("debate", should_continue_debate, {
        "debate": "debate",
        "moderator": "moderator",
    })

    # Research loop (max 1 extra cycle)
    graph.add_conditional_edges("moderator", should_research_more, {
        "researcher": "researcher",
        "publisher": "publisher",
    })

    # Evaluation loop (max 1 rerun)
    graph.add_edge("publisher", "evaluator")
    graph.add_conditional_edges("evaluator", should_rerun_publisher, {
        "publisher": "publisher",
        "end": END,
    })

    return graph.compile()

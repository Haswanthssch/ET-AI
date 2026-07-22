"""
AURA-EPC Module 3: RFI Intelligence Copilot
Conversational RAG agent for site engineers.
Retrieves relevant historical RFIs and generates answers with inline citations.

Endpoint: POST /api/v1/rfi-copilot
"""
from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from backend.core.groq_client import chat_complete
from backend.core.vector_store import get_vector_store


# ---------------------------------------------------------------------------
# State Schema
# ---------------------------------------------------------------------------
class RFIState(TypedDict):
    query: str
    conversation_history: list[dict]
    retrieved_rfis: list[dict]
    answer: str
    citations: list[str]
    iteration: int


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------
async def retrieve_rfis(state: RFIState) -> RFIState:
    """Semantic search over indexed RFI logs."""
    store = get_vector_store()
    results = store.search(state["query"], top_k=5)
    state["retrieved_rfis"] = [
        {
            "doc_id": r.doc_id,
            "source": r.source,
            "content": r.content,
            "score": round(r.score, 3),
        }
        for r in results
    ]
    return state


async def generate_rfi_answer(state: RFIState) -> RFIState:
    """Generate a cited answer using retrieved RFIs and conversation context."""
    rfi_context = "\n\n".join(
        f"[Source: {r['doc_id']}]\n{r['content']}"
        for r in state["retrieved_rfis"]
    )

    history_text = ""
    for msg in state["conversation_history"][-6:]:  # last 3 turns
        role = msg.get("role", "user")
        history_text += f"{role.upper()}: {msg.get('content', '')}\n"

    system_prompt = """You are AURA RFI Copilot, an intelligent assistant for site and field engineers on a hyperscale data center EPC project.

Your role is to:
1. Answer engineering questions by referencing historical RFI resolutions.
2. Always cite your sources inline using the format [Source: RFI-XXX].
3. If the retrieved context doesn't answer the question, say so clearly.
4. Keep answers technically precise and actionable.
5. If relevant, mention the specification section (TIA-942, ASHRAE, NFPA) that governs the issue."""

    user_prompt = f"""RETRIEVED RFI CONTEXT:
{rfi_context}

CONVERSATION HISTORY:
{history_text}

CURRENT QUESTION: {state['query']}

Provide a technically accurate, cited answer to the question based on the retrieved RFIs."""

    answer = await chat_complete(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    # Extract citations from answer text
    import re
    citations = re.findall(r"\[Source: (RFI-\d+|TIA-\w+|ASHRAE[\w-]+|NFPA[\w-]+)\]", answer)
    state["answer"] = answer
    state["citations"] = list(set(citations))
    return state


async def rfi_critic(state: RFIState) -> RFIState:
    """Critic: ensure the answer contains at least one citation."""
    state["iteration"] = state.get("iteration", 0) + 1
    if not state["citations"] and state["iteration"] < 2 and state["retrieved_rfis"]:
        # Force a re-generation with a reminder to cite
        state["query"] = state["query"] + " [IMPORTANT: You MUST include inline citations like [Source: RFI-001]]"
    return state


def route_rfi_critic(state: RFIState) -> str:
    if not state["citations"] and state["iteration"] < 2:
        return "generate"
    return END


# ---------------------------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------------------------
def build_rfi_graph():
    builder = StateGraph(RFIState)
    builder.add_node("retrieve", retrieve_rfis)
    builder.add_node("generate", generate_rfi_answer)
    builder.add_node("critic", rfi_critic)

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", "critic")
    builder.add_conditional_edges(
        "critic", route_rfi_critic, {"generate": "generate", END: END}
    )

    return builder.compile()


_rfi_graph = None


async def run_rfi_copilot(
    query: str,
    conversation_history: list[dict] | None = None,
) -> dict[str, Any]:
    global _rfi_graph
    if _rfi_graph is None:
        _rfi_graph = build_rfi_graph()

    initial_state: RFIState = {
        "query": query,
        "conversation_history": conversation_history or [],
        "retrieved_rfis": [],
        "answer": "",
        "citations": [],
        "iteration": 0,
    }

    result = await _rfi_graph.ainvoke(initial_state)
    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "sources": [
            {"id": r["doc_id"], "score": r["score"], "excerpt": r["content"][:200] + "..."}
            for r in result["retrieved_rfis"]
        ],
        "self_healing_triggered": result["iteration"] > 1,
    }


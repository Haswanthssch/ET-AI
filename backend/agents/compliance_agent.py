"""
AURA-EPC Module 1: Compliance Agent
LangGraph stateful agent that performs RAG-based compliance checking of
vendor submittals against TIA-942/ASHRAE standards stored in FAISS.

Endpoint: POST /api/v1/compliance
"""
from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

from backend.core.groq_client import chat_complete
from backend.core.vector_store import get_vector_store


# ---------------------------------------------------------------------------
# State Schema
# ---------------------------------------------------------------------------
class ComplianceState(TypedDict):
    submittal_text: str
    spec_results: list[dict]
    findings: list[dict]
    verdict: str
    critique: str
    iteration: int
    final_report: dict


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------
async def retrieve_specs(state: ComplianceState) -> ComplianceState:
    """RAG retrieval: find relevant spec sections for the submittal text."""
    store = get_vector_store()
    results = store.search(state["submittal_text"], top_k=6)
    state["spec_results"] = [
        {"source": r.source, "doc_id": r.doc_id, "content": r.content, "score": r.score}
        for r in results
    ]
    return state


async def analyze_compliance(state: ComplianceState) -> ComplianceState:
    """Use Groq LLM to analyze submittal against retrieved specs."""
    spec_context = "\n\n".join(
        f"[{r['source']} — {r['doc_id']}]\n{r['content']}"
        for r in state["spec_results"]
    )

    prompt = f"""You are a senior EPC Compliance Engineer reviewing a vendor submittal against TIA-942 and ASHRAE standards.

VENDOR SUBMITTAL TEXT:
{state['submittal_text']}

RELEVANT SPECIFICATION SECTIONS:
{spec_context}

Analyze the submittal carefully and identify:
1. CONFORMANCES: Where the submittal meets the specification.
2. NON-CONFORMANCES: Specific deviations with exact spec section references (e.g., "Voltage tolerance ±8% exceeds TIA-942-B §7.3.4 limit of ±5%").
3. OBSERVATIONS: Minor concerns or items requiring clarification.

Format your response as a structured JSON object with keys:
- "conformances": [list of strings]
- "non_conformances": [list of objects with "finding", "spec_ref", "severity" (Critical/Major/Minor)]
- "observations": [list of strings]
- "overall_verdict": "COMPLIANT" | "NON-COMPLIANT" | "CONDITIONALLY-COMPLIANT"
- "recommended_action": string

Respond with ONLY the JSON object, no markdown fences."""

    response = await chat_complete(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000,
    )

    try:
        import json
        findings = json.loads(response)
    except Exception:
        findings = {
            "conformances": [],
            "non_conformances": [{"finding": response, "spec_ref": "N/A", "severity": "Major"}],
            "observations": [],
            "overall_verdict": "NON-COMPLIANT",
            "recommended_action": "Manual review required — LLM parse error.",
        }

    state["findings"] = findings.get("non_conformances", [])
    state["verdict"] = findings.get("overall_verdict", "UNKNOWN")
    state["final_report"] = findings
    return state


async def critic_node(state: ComplianceState) -> ComplianceState:
    """
    Critic/Self-Healing Node: Reviews the compliance analysis for completeness.
    If iteration > 1, skip to avoid infinite loops.
    """
    if state["iteration"] >= 1:
        state["critique"] = "APPROVED"
        return state

    non_conformances = state.get("findings", [])
    if not non_conformances and state["verdict"] == "COMPLIANT":
        # Check if the LLM missed obvious issues
        critique_prompt = f"""Review this compliance verdict "COMPLIANT" for the following submittal:
{state['submittal_text'][:500]}

Is this verdict plausible given typical data center equipment submissions?
Reply with just "APPROVED" or "NEEDS_RECHECK: <reason>"."""

        critique = await chat_complete(
            messages=[{"role": "user", "content": critique_prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        state["critique"] = critique.strip()
    else:
        state["critique"] = "APPROVED"

    state["iteration"] = state.get("iteration", 0) + 1
    return state


def route_after_critic(state: ComplianceState) -> str:
    """Route back to analyze if critique demands a recheck, otherwise end."""
    if state["critique"].startswith("NEEDS_RECHECK") and state["iteration"] < 2:
        return "analyze"
    return END


# ---------------------------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------------------------
def build_compliance_graph() -> StateGraph:
    builder = StateGraph(ComplianceState)
    builder.add_node("retrieve", retrieve_specs)
    builder.add_node("analyze", analyze_compliance)
    builder.add_node("critic", critic_node)

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "analyze")
    builder.add_edge("analyze", "critic")
    builder.add_conditional_edges("critic", route_after_critic, {"analyze": "analyze", END: END})

    return builder.compile()


_compliance_graph = None


async def run_compliance_check(submittal_text: str) -> dict[str, Any]:
    """Public API: run the compliance agent on a submittal text."""
    global _compliance_graph
    if _compliance_graph is None:
        _compliance_graph = build_compliance_graph()

    initial_state: ComplianceState = {
        "submittal_text": submittal_text,
        "spec_results": [],
        "findings": [],
        "verdict": "",
        "critique": "",
        "iteration": 0,
        "final_report": {},
    }

    result = await _compliance_graph.ainvoke(initial_state)
    return {
        "verdict": result["verdict"],
        "report": result["final_report"],
        "specs_referenced": [r["source"] + " — " + r["doc_id"] for r in result["spec_results"]],
        "self_healing_triggered": result["iteration"] > 1,
    }


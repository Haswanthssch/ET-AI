"""
AURA-EPC Module 2: Predictive Risk Engine
LangGraph agent that:
  1. Reads supply chain delays
  2. Runs NetworkX CPM cascade analysis
  3. Scores delay probability via XGBoost
  4. Generates 3 mitigation workarounds via Groq

Endpoint: POST /api/v1/predict-risk
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

import pandas as pd

from backend.core.groq_client import chat_complete
from backend.core.cpm_engine import get_cpm_engine
from backend.core.ml_model import predict_delay_probability
from langgraph.graph import StateGraph, END


# ---------------------------------------------------------------------------
# State Schema
# ---------------------------------------------------------------------------
class RiskState(TypedDict):
    equipment_tag: str
    task_id: str | None
    supply_delay_days: int
    supply_status: str
    cpm_analysis: dict
    delay_probability: float
    risk_level: str
    mitigations: list[str]
    final_report: dict
    iteration: int


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------
async def load_supply_impact(state: RiskState) -> RiskState:
    """
    Load supply chain context and link to the schedule task via equipment tag.
    """
    supply_csv = Path("./data/supply_chain.csv")
    cpm = get_cpm_engine()

    task_id = state.get("task_id")
    equipment_tag = state.get("equipment_tag", "")

    # Try to find linked task from supply CSV
    if supply_csv.exists() and not task_id:
        df = pd.read_csv(supply_csv)
        row = df[df["equipment_tag"] == equipment_tag]
        if not row.empty:
            linked = str(row.iloc[0].get("linked_task", ""))
            if linked and linked != "nan":
                task_id = linked
            state["supply_delay_days"] = int(row.iloc[0].get("delay_days", 0))
            state["supply_status"] = str(row.iloc[0].get("status", "On Track"))

    state["task_id"] = task_id
    return state


async def run_cpm_analysis(state: RiskState) -> RiskState:
    """Compute cascade impact of the supply delay on the project schedule."""
    cpm = get_cpm_engine()
    task_id = state.get("task_id")

    if not task_id:
        # No linked task — minimal impact
        state["cpm_analysis"] = {
            "message": "No schedule task linked to this equipment tag.",
            "project_slip_days": 0,
        }
        return state

    delay_days = state.get("supply_delay_days", 0)
    cascade = cpm.apply_delay(task_id, delay_days)
    state["cpm_analysis"] = cascade
    return state


async def score_risk(state: RiskState) -> RiskState:
    """Run XGBoost to predict delay probability."""
    cpm = get_cpm_engine()
    task_id = state.get("task_id")
    task = cpm.get_task(task_id) if task_id else None

    features = {
        "duration_days": task.duration if task else 14,
        "float_days": task.float_days if task else 0,
        "is_critical": int(task.is_critical) if task else 0,
        "phase": task.phase if task else "UNKNOWN",
        "lead_time_days": 120,
        "supply_delay_days": state.get("supply_delay_days", 0),
        "supply_status": state.get("supply_status", "On Track"),
        "has_equipment": 1 if state.get("equipment_tag") else 0,
    }

    prob = predict_delay_probability(features)
    state["delay_probability"] = prob

    if prob >= 0.75:
        state["risk_level"] = "CRITICAL"
    elif prob >= 0.50:
        state["risk_level"] = "HIGH"
    elif prob >= 0.25:
        state["risk_level"] = "MEDIUM"
    else:
        state["risk_level"] = "LOW"

    return state


async def generate_mitigations(state: RiskState) -> RiskState:
    """Use Groq to generate 3 operational mitigation workarounds."""
    cpm_info = state["cpm_analysis"]
    prompt = f"""You are a Senior EPC Project Controls Manager for a hyperscale data center build.

RISK SCENARIO:
- Equipment Tag: {state['equipment_tag']}
- Supply Status: {state['supply_status']}
- Supply Delay: {state['supply_delay_days']} days
- Linked Schedule Task: {state.get('task_id', 'N/A')}
- Delay Probability (ML): {state['delay_probability']:.0%}
- Risk Level: {state['risk_level']}
- Project Schedule Slip: {cpm_info.get('project_slip_days', 0)} days
- Critical Path Impacted Tasks: {cpm_info.get('critical_path_impacted_tasks', 0)}

Generate exactly 3 specific, actionable operational mitigation workarounds to recover the schedule.
Each mitigation should be a concrete action (not generic advice).

Format as a JSON array of 3 strings. Example:
["Action 1 with specifics...", "Action 2 with specifics...", "Action 3 with specifics..."]

Respond with ONLY the JSON array."""

    response = await chat_complete(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800,
    )

    try:
        mitigations = json.loads(response)
        if not isinstance(mitigations, list):
            raise ValueError("Not a list")
    except Exception:
        mitigations = [
            f"Expedite alternative sourcing for {state['equipment_tag']} from secondary vendor with equivalent spec.",
            f"Re-sequence schedule to front-load non-dependent critical path tasks, absorbing {state['supply_delay_days']} days.",
            "Engage customs broker immediately to clear port hold; provide all documentation for same-day submission.",
        ]

    state["mitigations"] = mitigations[:3]
    state["final_report"] = {
        "equipment_tag": state["equipment_tag"],
        "supply_status": state["supply_status"],
        "supply_delay_days": state["supply_delay_days"],
        "delay_probability": round(state["delay_probability"], 3),
        "risk_level": state["risk_level"],
        "cpm_cascade": cpm_info,
        "mitigations": state["mitigations"],
    }
    return state


async def risk_critic(state: RiskState) -> RiskState:
    """Self-healing critic: verify mitigations are substantive."""
    state["iteration"] = state.get("iteration", 0) + 1
    if state["iteration"] >= 2:
        return state

    mitigations = state.get("mitigations", [])
    if len(mitigations) < 3 or any(len(m) < 30 for m in mitigations):
        # Mitigations too thin — regenerate (handled by conditional edge)
        state["mitigations"] = []
    return state


def route_risk_critic(state: RiskState) -> str:
    if not state.get("mitigations") and state.get("iteration", 0) < 2:
        return "mitigate"
    return END


# ---------------------------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------------------------
def build_risk_graph():
    builder = StateGraph(RiskState)
    builder.add_node("load_supply", load_supply_impact)
    builder.add_node("cpm", run_cpm_analysis)
    builder.add_node("score", score_risk)
    builder.add_node("mitigate", generate_mitigations)
    builder.add_node("critic", risk_critic)

    builder.set_entry_point("load_supply")
    builder.add_edge("load_supply", "cpm")
    builder.add_edge("cpm", "score")
    builder.add_edge("score", "mitigate")
    builder.add_edge("mitigate", "critic")
    builder.add_conditional_edges("critic", route_risk_critic, {"mitigate": "mitigate", END: END})

    return builder.compile()


_risk_graph = None


async def run_risk_prediction(equipment_tag: str, task_id: str | None = None) -> dict[str, Any]:
    global _risk_graph
    if _risk_graph is None:
        _risk_graph = build_risk_graph()

    initial_state: RiskState = {
        "equipment_tag": equipment_tag,
        "task_id": task_id,
        "supply_delay_days": 0,
        "supply_status": "Unknown",
        "cpm_analysis": {},
        "delay_probability": 0.0,
        "risk_level": "LOW",
        "mitigations": [],
        "final_report": {},
        "iteration": 0,
    }

    result = await _risk_graph.ainvoke(initial_state)
    return result["final_report"]


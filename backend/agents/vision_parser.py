"""
AURA-EPC Module 5: Computer Vision Blueprint Parser
Uses Groq's vision model to analyze uploaded P&ID diagrams and shop drawings.
Extracts equipment tags and detects layout deviations.

Endpoint: POST /api/v1/vision-parse
"""
from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from backend.core.groq_client import vision_complete, chat_complete


# ---------------------------------------------------------------------------
# State Schema
# ---------------------------------------------------------------------------
class VisionState(TypedDict):
    image_bytes: bytes
    image_mime: str
    filename: str
    raw_vision_output: str
    extracted_data: dict
    deviation_analysis: dict
    summary: str
    iteration: int


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------
async def analyze_blueprint(state: VisionState) -> VisionState:
    """Send P&ID/shop drawing to Groq vision model for analysis."""
    prompt = """You are an expert P&ID and engineering drawing analyst for a hyperscale data center EPC project.

Analyze this engineering drawing carefully and extract:

1. EQUIPMENT TAGS: All visible equipment identifiers (e.g., AHU-01, UPS-B2, GEN-CAT-01, CRAC-03).
   Format: [{"tag": "TAG-ID", "description": "Equipment description", "location": "Room/zone if visible"}]

2. LINE TYPES: Identify pipe/cable line types (cooling water, power, data, drain, etc.)

3. LAYOUT ISSUES: Any apparent deviations, clearance violations, or conflicts visible in the drawing.
   Common issues: insufficient maintenance clearance, improper pipe routing, missing isolation valves, 
   code violation indicators, drawing revision discrepancies.

4. DRAWING METADATA: Drawing number, revision, date, scale (if visible).

5. SYSTEM TYPE: Identify what system this drawing depicts (Electrical SLD, Piping P&ID, HVAC Layout, etc.)

Respond with a structured JSON object:
{
  "system_type": "string",
  "drawing_metadata": {"number": null, "revision": null, "date": null, "scale": null, "title": null},
  "equipment_tags": [{"tag": "string", "description": "string", "location": "string"}],
  "line_types": ["string"],
  "layout_deviations": [{"issue": "string", "location": "string", "severity": "Critical|Major|Minor", "spec_ref": "string"}],
  "observations": ["string"],
  "confidence": 0.0-1.0
}

Respond with ONLY the JSON object."""

    raw = await vision_complete(
        prompt=prompt,
        image_bytes=state["image_bytes"],
        image_mime=state["image_mime"],
    )
    state["raw_vision_output"] = raw
    return state


async def parse_vision_output(state: VisionState) -> VisionState:
    """Parse and validate the vision model's JSON output."""
    raw = state["raw_vision_output"]
    try:
        # Strip markdown code fences if present
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        extracted = json.loads(clean.strip())
    except Exception:
        # Fallback: ask text model to fix the JSON
        fix_prompt = f"""The following text was supposed to be a JSON object but has formatting issues.
Fix it and return ONLY valid JSON:

{raw[:2000]}"""
        fixed = await chat_complete(
            messages=[{"role": "user", "content": fix_prompt}],
            temperature=0.0,
            max_tokens=2000,
        )
        try:
            extracted = json.loads(fixed)
        except Exception:
            extracted = {
                "system_type": "Unknown",
                "drawing_metadata": {},
                "equipment_tags": [],
                "line_types": [],
                "layout_deviations": [],
                "observations": [f"Vision output parse error: {raw[:200]}"],
                "confidence": 0.0,
            }

    state["extracted_data"] = extracted
    state["iteration"] = state.get("iteration", 0) + 1
    return state


async def generate_deviation_report(state: VisionState) -> VisionState:
    """Generate a professional deviation report from extracted data."""
    extracted = state["extracted_data"]
    deviations = extracted.get("layout_deviations", [])
    equipment_tags = extracted.get("equipment_tags", [])

    summary_prompt = f"""You are a senior EPC drawing review engineer.
Based on the following P&ID/blueprint analysis results, write a concise executive summary (3-4 sentences):

- System Type: {extracted.get('system_type', 'Unknown')}
- Equipment Tags Found: {len(equipment_tags)} items — {', '.join(t['tag'] for t in equipment_tags[:10])}
- Layout Deviations: {len(deviations)} issues found
- Critical Issues: {len([d for d in deviations if d.get('severity') == 'Critical'])}
- Drawing: {extracted.get('drawing_metadata', {}).get('title', 'N/A')} Rev {extracted.get('drawing_metadata', {}).get('revision', 'N/A')}

Write the summary as a professional engineering statement."""

    summary = await chat_complete(
        messages=[{"role": "user", "content": summary_prompt}],
        temperature=0.1,
        max_tokens=300,
    )

    state["deviation_analysis"] = {
        "total_deviations": len(deviations),
        "critical": len([d for d in deviations if d.get("severity") == "Critical"]),
        "major": len([d for d in deviations if d.get("severity") == "Major"]),
        "minor": len([d for d in deviations if d.get("severity") == "Minor"]),
        "deviations": deviations,
    }
    state["summary"] = summary
    return state


# ---------------------------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------------------------
def build_vision_graph():
    builder = StateGraph(VisionState)
    builder.add_node("analyze", analyze_blueprint)
    builder.add_node("parse", parse_vision_output)
    builder.add_node("report", generate_deviation_report)

    builder.set_entry_point("analyze")
    builder.add_edge("analyze", "parse")
    builder.add_edge("parse", "report")
    builder.add_edge("report", END)

    return builder.compile()


_vision_graph = None


async def run_vision_parse(
    image_bytes: bytes,
    image_mime: str = "image/png",
    filename: str = "drawing.png",
) -> dict[str, Any]:
    global _vision_graph
    if _vision_graph is None:
        _vision_graph = build_vision_graph()

    initial_state: VisionState = {
        "image_bytes": image_bytes,
        "image_mime": image_mime,
        "filename": filename,
        "raw_vision_output": "",
        "extracted_data": {},
        "deviation_analysis": {},
        "summary": "",
        "iteration": 0,
    }

    result = await _vision_graph.ainvoke(initial_state)
    return {
        "filename": filename,
        "system_type": result["extracted_data"].get("system_type", "Unknown"),
        "drawing_metadata": result["extracted_data"].get("drawing_metadata", {}),
        "equipment_tags": result["extracted_data"].get("equipment_tags", []),
        "line_types": result["extracted_data"].get("line_types", []),
        "deviation_analysis": result["deviation_analysis"],
        "observations": result["extracted_data"].get("observations", []),
        "confidence": result["extracted_data"].get("confidence", 0.0),
        "summary": result["summary"],
    }


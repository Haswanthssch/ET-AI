"""
AURA-EPC Module 4: Commissioning QA Copilot
Parses site test logs and checks them against Uptime Institute Tier thresholds.
Auto-generates a Tier compliance certificate.

Endpoint: POST /api/v1/commissioning
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from backend.core.groq_client import chat_complete
from backend.core.config import settings


# ---------------------------------------------------------------------------
# Uptime Institute Tier Thresholds
# ---------------------------------------------------------------------------
TIER_CRITERIA = {
    "I": {
        "availability_pct": settings.TIER_I_AVAILABILITY,
        "redundancy": "N",
        "concurrent_maintainability": False,
        "fault_tolerance": False,
        "allowed_downtime_hours": 28.8,
        "description": "Basic Site Infrastructure",
    },
    "II": {
        "availability_pct": settings.TIER_II_AVAILABILITY,
        "redundancy": "N+1 (partial)",
        "concurrent_maintainability": False,
        "fault_tolerance": False,
        "allowed_downtime_hours": 22.7,
        "description": "Redundant Site Infrastructure Components",
    },
    "III": {
        "availability_pct": settings.TIER_III_AVAILABILITY,
        "redundancy": "N+1",
        "concurrent_maintainability": True,
        "fault_tolerance": False,
        "allowed_downtime_hours": 1.6,
        "description": "Concurrently Maintainable Site Infrastructure",
    },
    "IV": {
        "availability_pct": settings.TIER_IV_AVAILABILITY,
        "redundancy": "2N",
        "concurrent_maintainability": True,
        "fault_tolerance": True,
        "allowed_downtime_hours": 0.4,
        "description": "Fault-Tolerant Site Infrastructure",
    },
}


# ---------------------------------------------------------------------------
# State Schema
# ---------------------------------------------------------------------------
class CommissioningState(TypedDict):
    test_log_text: str
    target_tier: str
    parsed_metrics: dict
    tier_analysis: dict
    certificate: dict
    issues: list[dict]
    overall_pass: bool
    iteration: int


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------
async def parse_test_log(state: CommissioningState) -> CommissioningState:
    """Use Groq to extract structured test metrics from raw log text."""
    prompt = f"""You are a commissioning QA specialist. Parse the following site test log and extract structured metrics.

TEST LOG:
{state['test_log_text']}

Extract and return a JSON object with the following fields (use null if not found):
{{
  "generator_test": {{
    "load_bank_kva": number or null,
    "transfer_time_seconds": number or null,
    "voltage_tolerance_pct": number or null,
    "runtime_hours": number or null,
    "result": "PASS" | "FAIL" | null
  }},
  "ups_test": {{
    "runtime_minutes": number or null,
    "output_thd_pct": number or null,
    "input_voltage": number or null,
    "result": "PASS" | "FAIL" | null
  }},
  "cooling_test": {{
    "supply_temp_celsius": number or null,
    "humidity_rh_pct": number or null,
    "pue": number or null,
    "result": "PASS" | "FAIL" | null
  }},
  "network_test": {{
    "latency_ms": number or null,
    "packet_loss_pct": number or null,
    "result": "PASS" | "FAIL" | null
  }},
  "fire_suppression_test": {{
    "detection_time_seconds": number or null,
    "agent_discharge_time_seconds": number or null,
    "result": "PASS" | "FAIL" | null
  }},
  "grounding_test": {{
    "resistance_ohms": number or null,
    "result": "PASS" | "FAIL" | null
  }},
  "site_availability_pct": number or null,
  "concurrent_maintenance_verified": boolean or null,
  "fault_tolerance_verified": boolean or null,
  "test_date": string or null,
  "test_engineer": string or null
}}

Respond with ONLY the JSON object."""

    response = await chat_complete(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1500,
    )

    try:
        metrics = json.loads(response)
    except Exception:
        metrics = {"parse_error": response[:200]}

    state["parsed_metrics"] = metrics
    return state


async def check_tier_compliance(state: CommissioningState) -> CommissioningState:
    """
    Check extracted metrics against Uptime Institute Tier thresholds.
    """
    tier = state["target_tier"].upper()
    criteria = TIER_CRITERIA.get(tier, TIER_CRITERIA["III"])
    metrics = state["parsed_metrics"]
    issues = []
    checks = []

    # --- Generator checks ---
    gen = metrics.get("generator_test", {}) or {}
    if gen.get("transfer_time_seconds") is not None:
        if gen["transfer_time_seconds"] > 10:
            issues.append({
                "system": "Generator",
                "finding": f"Transfer time {gen['transfer_time_seconds']}s exceeds TIA-942-B §7.3.4 limit of 10s",
                "severity": "Critical",
            })
        else:
            checks.append({"system": "Generator Transfer", "status": "PASS"})

    if gen.get("voltage_tolerance_pct") is not None:
        if gen["voltage_tolerance_pct"] > 5:
            issues.append({
                "system": "Generator",
                "finding": f"Voltage tolerance ±{gen['voltage_tolerance_pct']}% exceeds TIA-942-B ±5% limit",
                "severity": "Major",
            })
        else:
            checks.append({"system": "Generator Voltage", "status": "PASS"})

    # --- UPS checks ---
    ups = metrics.get("ups_test", {}) or {}
    if ups.get("runtime_minutes") is not None:
        if ups["runtime_minutes"] < 10:
            issues.append({
                "system": "UPS",
                "finding": f"UPS runtime {ups['runtime_minutes']}min < TIA-942-B §7.2.1 minimum 10min",
                "severity": "Critical",
            })
        else:
            checks.append({"system": "UPS Runtime", "status": "PASS"})

    if ups.get("output_thd_pct") is not None:
        if ups["output_thd_pct"] > 5:
            issues.append({
                "system": "UPS",
                "finding": f"THDv {ups['output_thd_pct']}% exceeds TIA-942-B §7.2.1 limit of 5%",
                "severity": "Major",
            })
        else:
            checks.append({"system": "UPS THD", "status": "PASS"})

    # --- Cooling checks ---
    cool = metrics.get("cooling_test", {}) or {}
    if cool.get("supply_temp_celsius") is not None:
        temp = cool["supply_temp_celsius"]
        if not (18 <= temp <= 27):
            issues.append({
                "system": "Cooling",
                "finding": f"Supply temp {temp}°C outside ASHRAE A1 range 18–27°C",
                "severity": "Major",
            })
        else:
            checks.append({"system": "Cooling Temp", "status": "PASS"})

    if cool.get("pue") is not None:
        if cool["pue"] > 1.4:
            issues.append({
                "system": "Cooling",
                "finding": f"PUE {cool['pue']} exceeds ASHRAE 90.4 target of ≤1.4",
                "severity": "Minor",
            })
        else:
            checks.append({"system": "PUE", "status": "PASS"})

    # --- Grounding ---
    gnd = metrics.get("grounding_test", {}) or {}
    if gnd.get("resistance_ohms") is not None:
        if gnd["resistance_ohms"] > 1.0:
            issues.append({
                "system": "Grounding",
                "finding": f"Ground resistance {gnd['resistance_ohms']}Ω exceeds TIA-942-B §7.4.3 limit of 1Ω",
                "severity": "Critical",
            })
        else:
            checks.append({"system": "Grounding", "status": "PASS"})

    # --- Tier-specific checks ---
    if tier in ["III", "IV"] and criteria["concurrent_maintainability"]:
        if metrics.get("concurrent_maintenance_verified") is False:
            issues.append({
                "system": "Maintainability",
                "finding": "Concurrent maintainability not verified — required for Tier III/IV",
                "severity": "Critical",
            })
        elif metrics.get("concurrent_maintenance_verified"):
            checks.append({"system": "Concurrent Maintainability", "status": "PASS"})

    # --- Overall availability ---
    if metrics.get("site_availability_pct") is not None:
        avail = metrics["site_availability_pct"]
        required = criteria["availability_pct"]
        if avail < required:
            issues.append({
                "system": "Availability",
                "finding": f"Site availability {avail}% below Tier {tier} requirement of {required}%",
                "severity": "Critical",
            })
        else:
            checks.append({"system": "Availability", "status": "PASS"})

    critical_issues = [i for i in issues if i["severity"] == "Critical"]
    state["issues"] = issues
    state["overall_pass"] = len(critical_issues) == 0
    state["tier_analysis"] = {
        "target_tier": tier,
        "criteria": criteria,
        "passed_checks": checks,
        "failed_checks": issues,
        "critical_failures": len(critical_issues),
        "overall_pass": state["overall_pass"],
    }
    return state


async def generate_certificate(state: CommissioningState) -> CommissioningState:
    """Generate a Tier compliance certificate using Groq."""
    tier = state["target_tier"]
    passed = state["overall_pass"]
    metrics = state["parsed_metrics"]
    issues = state["issues"]

    prompt = f"""You are a Senior Commissioning QA Authority for an Uptime Institute Tier {tier} data center.

COMMISSIONING TEST RESULTS:
- Target Tier: Tier {tier}
- Overall Result: {"PASSED" if passed else "FAILED — NOT CERTIFIED"}
- Critical Failures: {len([i for i in issues if i["severity"] == "Critical"])}
- Total Issues Found: {len(issues)}
- Test Date: {metrics.get('test_date', datetime.now().strftime('%Y-%m-%d'))}
- Test Engineer: {metrics.get('test_engineer', 'AURA-EPC QA System')}

ISSUES:
{json.dumps(issues, indent=2)}

Generate a formal commissioning compliance certificate.
Include:
1. Certificate header with date and project reference
2. Summary of systems tested and their results
3. Specific non-conformances that must be resolved (if any)
4. {"CERTIFICATION GRANTED" if passed else "CERTIFICATION WITHHELD — Corrective Actions Required"}
5. Sign-off section

Be formal and professional. This is a legal document."""

    certificate_text = await chat_complete(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1500,
    )

    state["certificate"] = {
        "tier": tier,
        "status": "CERTIFIED" if passed else "NOT-CERTIFIED",
        "issued_date": datetime.now().strftime("%Y-%m-%d"),
        "certificate_text": certificate_text,
        "issues_count": len(issues),
        "critical_failures": len([i for i in issues if i["severity"] == "Critical"]),
    }
    state["iteration"] = state.get("iteration", 0) + 1
    return state


# ---------------------------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------------------------
def build_commissioning_graph():
    builder = StateGraph(CommissioningState)
    builder.add_node("parse", parse_test_log)
    builder.add_node("check", check_tier_compliance)
    builder.add_node("certify", generate_certificate)

    builder.set_entry_point("parse")
    builder.add_edge("parse", "check")
    builder.add_edge("check", "certify")
    builder.add_edge("certify", END)

    return builder.compile()


_commissioning_graph = None


async def run_commissioning_qa(
    test_log_text: str,
    target_tier: str = "III",
) -> dict[str, Any]:
    global _commissioning_graph
    if _commissioning_graph is None:
        _commissioning_graph = build_commissioning_graph()

    initial_state: CommissioningState = {
        "test_log_text": test_log_text,
        "target_tier": target_tier,
        "parsed_metrics": {},
        "tier_analysis": {},
        "certificate": {},
        "issues": [],
        "overall_pass": False,
        "iteration": 0,
    }

    result = await _commissioning_graph.ainvoke(initial_state)
    return {
        "overall_pass": result["overall_pass"],
        "target_tier": target_tier,
        "parsed_metrics": result["parsed_metrics"],
        "tier_analysis": result["tier_analysis"],
        "certificate": result["certificate"],
    }


"""API v1 routers for AURA-EPC - DEMO MODE with fake data"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import random

router = APIRouter(prefix="/v1", tags=["v1"])


class RiskPredictionRequest(BaseModel):
    equipment_tag: str


class RFICopilotRequest(BaseModel):
    query: str
    conversation_history: Optional[List[dict]] = []


@router.post("/predict-risk")
async def predict_risk(req: RiskPredictionRequest):
    """Run risk prediction - DEMO MODE returns fake data"""
    tag = req.equipment_tag.upper()
    
    return {
        "equipment_tag": tag,
        "delay_probability": round(random.uniform(0.3, 0.95), 2),
        "risk_level": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
        "supply_status": random.choice(["In Transit", "Customs Hold", "Delivered", "Manufacturing"]),
        "supply_delay_days": random.randint(0, 45),
        "cpm_cascade": {
            "project_slip_days": random.randint(5, 30),
            "critical_path_impacted_tasks": random.randint(1, 5),
            "affected_phases": random.sample(["Civil", "Structural", "MEP", "Electrical"], k=random.randint(1, 3))
        },
        "mitigations": [
            f"Expedite alternative sourcing for {tag} from secondary vendor with equivalent spec",
            f"Re-sequence critical path to front-load non-dependent tasks, absorbing {random.randint(5, 20)} days",
            "Engage customs broker for priority clearance with full documentation package"
        ]
    }


@router.post("/rfi-copilot")
async def rfi_copilot(req: RFICopilotRequest):
    """Run RFI copilot query - DEMO MODE returns fake data"""
    query_lower = req.query.lower()
    
    # Demo fake response based on query
    if "mep" in query_lower or "coordination" in query_lower:
        answer = "Based on historical RFI analysis, the MEP coordination conflict in IT Hall A was resolved by re-routing the chilled water supply line 18 inches above the cable tray, maintaining the required 4-inch separation per TIA-942-B §7.3.2. The resolution was approved on 2024-03-15 with no schedule impact."
        citations = ["RFI-1087", "TIA-942-B §7.3.2"]
    elif "tia" in query_lower or "cable tray" in query_lower:
        answer = "TIA-942-B requires minimum 4-inch horizontal separation between power and data cable trays, and 2-inch vertical separation. In raised floor environments, power must be routed in metallic conduit when within 24 inches of data cabling per §7.3.4."
        citations = ["TIA-942-B §7.3.2", "TIA-942-B §7.3.4"]
    elif "critical" in query_lower or "rfi" in query_lower:
        answer = "Found 6 critical priority RFIs related to electrical grounding: RFI-1087 (grounding busbar installation), RFI-1124 (earth pit resistance), RFI-1156 (lightning protection), RFI-1189 (bonding conductor), RFI-1203 (ground grid extension), and RFI-1245 (ESD flooring). All require same-day response per contract terms."
        citations = ["RFI-1087", "RFI-1124", "RFI-1156"]
    elif "seismic" in query_lower or "bracing" in query_lower:
        answer = "The seismic bracing non-compliance issue (RFI-1087) was resolved by installing additional lateral bracing at 8-foot intervals per IBC 2021 §13.3. The engineering team provided stamped drawings showing 4-point sway bracing for all cable tray crossings exceeding 6 meters."
        citations = ["RFI-1087", "IBC-2021 §13.3", "NFPA-70 §300.21"]
    else:
        answer = f"Based on analysis of 50 historical RFIs and TIA-942/ASHRAE specifications, I found 3 relevant documents addressing your query about '{req.query}'. The primary resolution involved coordination between MEP and structural teams, with approved deviation from specification §7.2.1 under engineering judgment."
        citations = ["RFI-1087", "TIA-942-B §7.2.1", "ASHRAE-90.4"]
    
    return {
        "answer": answer,
        "citations": citations,
        "sources": [
            {"id": c, "score": round(random.uniform(0.85, 0.99), 2), "excerpt": f"Excerpt from {c}..."}
            for c in citations
        ],
        "self_healing_triggered": False
    }


@router.post("/vision-parse")
async def vision_parse(file: UploadFile = File(...)):
    """Parse blueprint - DEMO MODE returns fake data"""
    return {
        "filename": file.filename or "upload",
        "system_type": random.choice(["Electrical SLD", "HVAC P&ID", "Piping Diagram", "Fire Suppression Layout"]),
        "drawing_metadata": {
            "number": f"DWG-{random.randint(1000, 9999)}",
            "revision": random.choice(["A", "B", "C", "0", "1"]),
            "date": "2024-03-15",
            "scale": random.choice(["1:50", "1:100", "1:200"]),
            "title": "Data Center MEP Layout"
        },
        "equipment_tags": [
            {"tag": f"AHU-{random.randint(1, 10):02d}", "description": "Air Handling Unit", "location": "Mechanical Floor"},
            {"tag": f"UPS-B{random.randint(1, 5)}", "description": "Uninterruptible Power Supply", "location": "Electrical Room"},
            {"tag": f"CRAC-{random.randint(1, 20):02d}", "description": "Computer Room Air Conditioner", "location": "Data Hall A"},
            {"tag": f"GEN-CAT-{random.randint(1, 5):02d}", "description": "Diesel Generator", "location": "External Plant"},
        ],
        "line_types": ["Power Cable", "Chilled Water", "Condenser Water", "Data Fiber", "Drain"],
        "deviation_analysis": {
            "total_deviations": random.randint(2, 5),
            "critical": random.randint(0, 2),
            "major": random.randint(1, 3),
            "minor": random.randint(0, 2),
            "deviations": [
                {
                    "issue": "Cable tray crossing within 12 inches of chilled water pipe - violates TIA-942-B §7.3.2 minimum 4-inch separation",
                    "location": "Gridline C, Level 2",
                    "severity": "Critical",
                    "spec_ref": "TIA-942-B §7.3.2"
                },
                {
                    "issue": "UPS battery room ventilation insufficient for 15-minute exhaust requirement",
                    "location": "Electrical Room B2",
                    "severity": "Major",
                    "spec_ref": "ASHRAE-90.4"
                },
                {
                    "issue": "Missing isolation valve on CRAC-03 condensate drain",
                    "location": "Mechanical Floor",
                    "severity": "Minor",
                    "spec_ref": "TIA-942-B §7.2.1"
                }
            ]
        },
        "observations": [
            "Drawing shows as-built conditions differ from design intent in 3 locations",
            "Revision history indicates 4 revisions - latest revision C dated 2024-03-10",
            "All equipment tags match the equipment schedule on Sheet E-101"
        ],
        "confidence": round(random.uniform(0.85, 0.98), 2),
        "summary": f"Analysis of {file.filename or 'blueprint'} reveals a {random.choice(['Electrical SLD', 'HVAC P&ID', 'Piping Diagram'])} with {random.randint(2, 5)} layout deviations identified. Critical issues include cable tray separation violations and insufficient ventilation. Equipment tagging is 95% complete with 4 major components identified."
    }


@router.post("/commissioning")
async def commissioning_qa(req: dict):
    """Commissioning QA - DEMO MODE returns fake data"""
    test_log = req.get("test_log_text", "")
    target_tier = req.get("target_tier", "III")
    
    # Demo fake response
    return {
        "overall_pass": True,
        "target_tier": target_tier,
        "parsed_metrics": {
            "generator_test": {
                "load_bank_kva": 2250,
                "transfer_time_seconds": 8.5,
                "voltage_tolerance_pct": 3.2,
                "runtime_hours": 24,
                "result": "PASS"
            },
            "ups_test": {
                "runtime_minutes": 45,
                "output_thd_pct": 3.8,
                "input_voltage": 480,
                "result": "PASS"
            },
            "cooling_test": {
                "supply_temp_celsius": 22.5,
                "humidity_rh_pct": 45,
                "pue": 1.28,
                "result": "PASS"
            },
            "network_test": {
                "latency_ms": 2.3,
                "packet_loss_pct": 0.0,
                "result": "PASS"
            },
            "grounding_test": {
                "resistance_ohms": 0.8,
                "result": "PASS"
            },
            "site_availability_pct": 99.985,
            "concurrent_maintenance_verified": True,
            "fault_tolerance_verified": True,
            "test_date": "2024-03-15",
            "test_engineer": "AURA-EPC QA System"
        },
        "tier_analysis": {
            "target_tier": target_tier,
            "criteria": {
                "availability_pct": 99.982,
                "redundancy": "N+1",
                "concurrent_maintainability": True,
                "fault_tolerance": False,
                "allowed_downtime_hours": 1.6,
                "description": "Concurrently Maintainable Site Infrastructure"
            },
            "passed_checks": [
                {"system": "Generator Transfer", "status": "PASS"},
                {"system": "Generator Voltage", "status": "PASS"},
                {"system": "UPS Runtime", "status": "PASS"},
                {"system": "UPS THD", "status": "PASS"},
                {"system": "Cooling Temp", "status": "PASS"},
                {"system": "PUE", "status": "PASS"},
                {"system": "Grounding", "status": "PASS"},
                {"system": "Concurrent Maintainability", "status": "PASS"},
                {"system": "Availability", "status": "PASS"}
            ],
            "failed_checks": [],
            "critical_failures": 0,
            "overall_pass": True
        },
        "certificate": {
            "tier": target_tier,
            "status": "CERTIFIED",
            "issued_date": "2024-03-15",
            "certificate_text": f"""UPTIME INSTITUTE TIER {target_tier} COMMISSIONING CERTIFICATE

Project: Hyperscale Data Center EPC
Certificate ID: CERT-2024-{random.randint(1000, 9999)}
Issue Date: 2024-03-15
Test Engineer: AURA-EPC QA System

This certifies that the above facility has successfully completed commissioning testing per Uptime Institute Tier {target_tier} requirements.

TEST RESULTS SUMMARY:
✓ Generator Transfer Time: 8.5s (TIA-942-B §7.3.4 compliant)
✓ UPS Runtime: 45 minutes (TIA-942-B §7.2.1 compliant)
✓ Cooling Supply Temp: 22.5°C (ASHRAE A1 compliant)
✓ PUE: 1.28 (ASHRAE 90.4 target met)
✓ Grounding Resistance: 0.8Ω (TIA-942-B §7.4.3 compliant)
✓ Site Availability: 99.985% (Tier {target_tier} requirement: 99.982%)

OVERALL RESULT: CERTIFIED
All critical tests passed. Facility meets Tier {target_tier} design specifications.

Authorized Signature: _______________________
Date: 2024-03-15""",
            "issues_count": 0,
            "critical_failures": 0
        }
    }


class ComplianceRequest(BaseModel):
    submittal_text: str
    equipment_tag: Optional[str] = None


@router.post("/compliance")
async def compliance_check(req: ComplianceRequest):
    """Spec & vendor compliance check - DEMO MODE returns fake data"""
    return {
        "equipment_tag": (req.equipment_tag or "SUBMITTAL").upper(),
        "verdict": "NON-COMPLIANT",
        "summary": "Vendor submittal reviewed against TIA-942-B and ASHRAE 90.4. "
                   "1 critical and 1 major deviation detected; requires resubmission.",
        "findings": [
            {
                "type": "non-conformance",
                "severity": "Critical",
                "description": "Voltage tolerance \u00b18% exceeds TIA-942-B \u00a77.3.4 limit of \u00b15%",
                "spec_ref": "TIA-942-B \u00a77.3.4",
            },
            {
                "type": "non-conformance",
                "severity": "Major",
                "description": "UPS battery room ventilation rate below 15-minute exhaust requirement",
                "spec_ref": "ASHRAE-90.4",
            },
            {
                "type": "observation",
                "severity": "Minor",
                "description": "Nameplate efficiency curve not provided for 25% load point",
                "spec_ref": "ASHRAE-90.4 \u00a76.5",
            },
        ],
        "conformances": [
            {"description": "Ingress protection rating IP54 meets specification", "spec_ref": "TIA-942-B \u00a77.2.1"},
            {"description": "Seismic anchorage certified to IBC 2021 Zone 4", "spec_ref": "IBC-2021 \u00a713.3"},
        ],
        "self_healing_triggered": True,
    }


@router.get("/supply-chain")
async def supply_chain():
    """Supply chain visibility - DEMO MODE returns fake data"""
    items = [
        {"tag": "GEN-CAT-01", "description": "Caterpillar 2500kVA Generator", "vendor": "Caterpillar",
         "status": "Customs Hold", "lead_time_days": 210, "delay_days": 18, "risk": "CRITICAL",
         "critical_path": True, "eta": "2024-05-02"},
        {"tag": "UPS-B1", "description": "800kVA Modular UPS", "vendor": "Vertiv",
         "status": "In Transit", "lead_time_days": 120, "delay_days": 4, "risk": "MEDIUM",
         "critical_path": True, "eta": "2024-04-18"},
        {"tag": "CRAC-07", "description": "Precision Cooling Unit", "vendor": "Stulz",
         "status": "Manufacturing", "lead_time_days": 90, "delay_days": 0, "risk": "LOW",
         "critical_path": False, "eta": "2024-04-25"},
        {"tag": "SWGR-M1", "description": "Main LV Switchgear", "vendor": "Schneider",
         "status": "Delivered", "lead_time_days": 150, "delay_days": 0, "risk": "LOW",
         "critical_path": True, "eta": "2024-03-01"},
        {"tag": "CT-04", "description": "Cooling Tower Cell", "vendor": "BAC",
         "status": "In Transit", "lead_time_days": 100, "delay_days": 7, "risk": "HIGH",
         "critical_path": False, "eta": "2024-04-30"},
    ]
    summary = {
        "total_items": len(items),
        "at_risk": sum(1 for i in items if i["risk"] in ("HIGH", "CRITICAL")),
        "on_critical_path": sum(1 for i in items if i["critical_path"]),
        "customs_holds": sum(1 for i in items if i["status"] == "Customs Hold"),
    }
    return {"summary": summary, "items": items}


@router.get("/executive-summary")
async def executive_summary():
    """Executive dashboard KPIs + live alerts - DEMO MODE returns fake data"""
    return {
        "project": "Hyperscale Data Centre \u2014 Phase 1 (24 MW)",
        "kpis": {
            "schedule_health_pct": 82,
            "project_slip_days": 18,
            "open_rfis": 12,
            "critical_ncrs": 3,
            "supply_items_at_risk": 2,
            "commissioning_progress_pct": 64,
            "budget_utilization_pct": 71,
        },
        "sla": {"rfi_response_hours_avg": 6.4, "rfi_sla_hours": 24, "on_time_pct": 91},
        "alerts": [
            {
                "severity": "Critical",
                "title": "GEN-CAT-01 on Customs Hold",
                "detail": "18-day delay cascades to critical path \u2014 projected 18-day project slip. "
                          "3 mitigation options generated.",
                "source": "Risk Engine",
                "equipment_tag": "GEN-CAT-01",
            },
            {
                "severity": "Major",
                "title": "Voltage tolerance non-conformance",
                "detail": "Generator submittal \u00b18% exceeds TIA-942-B \u00a77.3.4 \u00b15% limit.",
                "source": "Compliance Agent",
                "equipment_tag": "GEN-CAT-01",
            },
            {
                "severity": "Info",
                "title": "Tier III commissioning on track",
                "detail": "Data Hall A commissioning 64% complete; no critical failures.",
                "source": "Commissioning QA",
                "equipment_tag": None,
            },
        ],
        "risk_trend": [62, 65, 71, 68, 74, 79, 82],
        "phase_progress": [
            {"phase": "Civil", "pct": 100},
            {"phase": "Structural", "pct": 96},
            {"phase": "MEP", "pct": 74},
            {"phase": "Electrical", "pct": 58},
            {"phase": "Commissioning", "pct": 22},
        ],
    }
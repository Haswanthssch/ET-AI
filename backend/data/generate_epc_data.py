"""
AURA-EPC Data Hydration Script
Generates all synthetic project data required to bootstrap the system:
  1. master_schedule.csv  - 500-activity NetworkX DAG (24-month build)
  2. supply_chain.csv     - 50 equipment items (GEN-CAT-01 forced conflict)
  3. rfi_logs.json        - 50 realistic engineering conflict logs

Run: python generate_epc_data.py
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

DATA_DIR = Path(__file__).parent
random.seed(42)

# ---------------------------------------------------------------------------
# 1. MASTER SCHEDULE CSV
# ---------------------------------------------------------------------------
PHASES = [
    ("CIVIL", 0.18),
    ("STRUCTURAL", 0.10),
    ("MECHANICAL", 0.15),
    ("ELECTRICAL", 0.15),
    ("PLUMBING", 0.08),
    ("LOW_VOLTAGE", 0.08),
    ("COOLING", 0.10),
    ("COMMISSIONING", 0.10),
    ("CLOSEOUT", 0.06),
]

PHASE_EQUIPMENT_TAGS = {
    "CIVIL": ["FOUND-{:02d}", "GRND-{:02d}", "DRAIN-{:02d}"],
    "STRUCTURAL": ["STEEL-{:02d}", "CONC-{:02d}"],
    "MECHANICAL": ["AHU-{:02d}", "CRAC-{:02d}", "CHILLER-{:02d}", "PUMP-{:02d}"],
    "ELECTRICAL": ["XFMR-{:02d}", "SWGR-{:02d}", "UPS-{:02d}", "PDU-{:02d}"],
    "PLUMBING": ["PIPE-{:02d}", "VLVE-{:02d}"],
    "LOW_VOLTAGE": ["FIBER-{:02d}", "RACK-{:02d}", "PATCH-{:02d}"],
    "COOLING": ["CDU-{:02d}", "CRAC-C-{:02d}", "CTW-{:02d}"],
    "COMMISSIONING": ["CX-{:02d}", "ISCX-{:02d}"],
    "CLOSEOUT": ["DOC-{:02d}", "AS-BUILT-{:02d}"],
}

PHASE_TASK_NAMES = {
    "CIVIL": [
        "Site Survey & Geotechnical Assessment", "Earthworks & Excavation", "Pile Foundation Installation",
        "Concrete Slab Pour (Zone {})", "Underground Utility Routing", "Site Drainage System",
        "Perimeter Security Fencing", "Access Road Construction", "Retaining Wall Installation",
    ],
    "STRUCTURAL": [
        "Steel Frame Erection (Block {})", "Precast Panel Installation", "Metal Deck Installation",
        "Concrete Column Pour", "Secondary Steel Installation", "Roof Structure Assembly",
    ],
    "MECHANICAL": [
        "Air Handling Unit Installation (Room {})", "CRAC Unit Placement", "Chiller Plant Installation",
        "Cooling Tower Installation", "Pump Skid Assembly", "Piping Insulation", "Ductwork Fabrication",
        "Mechanical Penetrations Sealing",
    ],
    "ELECTRICAL": [
        "Medium Voltage Switchgear Installation (Zone {})", "Transformer Energization",
        "UPS System Installation (Row {})", "PDU Distribution Installation", "Generator Set Installation",
        "Emergency Power Transfer Testing", "Cable Tray Installation", "Grounding Grid Installation",
        "Busway Distribution (Zone {})", "PLC / SCADA Panel Installation",
    ],
    "PLUMBING": [
        "Domestic Water Main Installation", "Fire Suppression Piping (Zone {})",
        "Cooling Water Distribution Piping", "Condensate Drain System", "FM200 Clean Agent System",
    ],
    "LOW_VOLTAGE": [
        "Fiber Optic Backbone Installation", "Structured Cabling (Floor {})",
        "Security Camera System", "Access Control Panel Installation",
        "BMS Sensor Installation (Zone {})", "Network Cabinet Assembly (Row {})",
    ],
    "COOLING": [
        "CW Loop Flush & Chemical Treatment", "CDU Installation & Commissioning",
        "Precision Cooling Unit Integration", "Adiabatic Cooling System", "Thermal Storage Tank Installation",
    ],
    "COMMISSIONING": [
        "Factory Acceptance Testing (FAT) - UPS", "Site Acceptance Testing (SAT) - Cooling",
        "Integrated Systems Test (IST) - Power", "Tier III Uptime Institute Verification",
        "ASHRAE 90.4 Energy Baseline Check", "Generator Load Bank Testing",
        "Hot/Cold Aisle Containment Verification", "Network Latency Baseline",
    ],
    "CLOSEOUT": [
        "As-Built Drawing Compilation", "O&M Manual Handover",
        "Final Punch List Closeout", "Client Witness Testing", "Certificate of Occupancy",
    ],
}


def generate_schedule() -> list[dict]:
    """Generate 500 tasks as a networked DAG."""
    tasks = []
    task_id_counter = 1
    phase_task_ids: dict[str, list[str]] = {}

    for phase_name, fraction in PHASES:
        count = max(5, int(500 * fraction))
        phase_ids = []
        name_pool = PHASE_TASK_NAMES[phase_name]
        tag_templates = PHASE_EQUIPMENT_TAGS[phase_name]

        for i in range(count):
            tid = f"T-{task_id_counter:04d}"
            task_name = name_pool[i % len(name_pool)].format(i + 1) if "{}" in name_pool[i % len(name_pool)] else name_pool[i % len(name_pool)] + f" #{i + 1}"
            duration = random.randint(3, 25)
            tag_tmpl = random.choice(tag_templates)
            equipment_tag = tag_tmpl.format(i + 1) if "{" in tag_tmpl else tag_tmpl

            phase_ids.append(tid)
            tasks.append({
                "task_id": tid,
                "task_name": task_name,
                "phase": phase_name,
                "duration_days": duration,
                "equipment_tag": equipment_tag,
                "predecessors": "",
                "float_days": 0,
                "is_critical": 0,
            })
            task_id_counter += 1

        phase_task_ids[phase_name] = phase_ids

    # Wire up dependencies
    phase_order = [p[0] for p in PHASES]
    task_map = {t["task_id"]: t for t in tasks}

    for phase_idx, phase_name in enumerate(phase_order):
        ids = phase_task_ids[phase_name]
        # Within-phase sequential chain (first 30% of tasks)
        chain_count = max(1, len(ids) // 3)
        for i in range(1, chain_count):
            task_map[ids[i]]["predecessors"] = ids[i - 1]

        # Cross-phase: last task of previous phase feeds first of this phase
        if phase_idx > 0:
            prev_phase = phase_order[phase_idx - 1]
            prev_ids = phase_task_ids[prev_phase]
            task_map[ids[0]]["predecessors"] = prev_ids[-1]

    return tasks


def run_cpm_on_tasks(tasks: list[dict]) -> list[dict]:
    """Run CPM passes on the generated task list."""
    G = nx.DiGraph()
    task_map = {t["task_id"]: t for t in tasks}

    for t in tasks:
        G.add_node(t["task_id"])

    for t in tasks:
        if t["predecessors"]:
            for pred in str(t["predecessors"]).split(","):
                pred = pred.strip()
                if pred and pred in task_map:
                    G.add_edge(pred, t["task_id"])

    if not nx.is_directed_acyclic_graph(G):
        # Remove cycles by removing last edge in each cycle
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles:
            G.remove_edge(cycle[-1], cycle[0])

    # Forward pass
    es = {}
    ef = {}
    for nid in nx.topological_sort(G):
        t = task_map[nid]
        preds = list(G.predecessors(nid))
        es[nid] = max((ef[p] for p in preds), default=0)
        ef[nid] = es[nid] + t["duration_days"]

    project_end = max(ef.values())

    # Backward pass
    ls = {}
    lf = {}
    for nid in reversed(list(nx.topological_sort(G))):
        t = task_map[nid]
        succs = list(G.successors(nid))
        lf[nid] = min((ls[s] for s in succs), default=project_end)
        ls[nid] = lf[nid] - t["duration_days"]

    for t in tasks:
        tid = t["task_id"]
        float_val = ls[tid] - es[tid]
        t["float_days"] = float_val
        t["is_critical"] = int(float_val == 0)

    return tasks


def generate_master_schedule():
    print("[1/3] Generating master_schedule.csv (500 activities)...")
    tasks = generate_schedule()
    tasks = run_cpm_on_tasks(tasks)

    # Pad to exactly 500
    while len(tasks) < 500:
        tasks.append({
            "task_id": f"T-{len(tasks) + 1:04d}",
            "task_name": f"Contingency Buffer Task #{len(tasks) + 1}",
            "phase": "CLOSEOUT",
            "duration_days": random.randint(1, 5),
            "equipment_tag": f"BUF-{len(tasks):03d}",
            "predecessors": tasks[-1]["task_id"] if tasks else "",
            "float_days": 10,
            "is_critical": 0,
        })
    tasks = tasks[:500]

    fieldnames = ["task_id", "task_name", "phase", "duration_days", "equipment_tag",
                  "predecessors", "float_days", "is_critical"]
    out_path = DATA_DIR / "master_schedule.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tasks)
    print(f"    [OK] Saved {len(tasks)} tasks -> {out_path}")
    return tasks


# ---------------------------------------------------------------------------
# 2. SUPPLY CHAIN CSV
# ---------------------------------------------------------------------------
EQUIPMENT_CATEGORIES = [
    ("GENERATOR", ["GEN-CAT-01", "GEN-CAT-02", "GEN-CUM-01"]),
    ("UPS", ["UPS-EAT-01", "UPS-EAT-02", "UPS-SCH-01", "UPS-SCH-02"]),
    ("TRANSFORMER", ["XFMR-ABB-01", "XFMR-ABB-02", "XFMR-GE-01"]),
    ("SWITCHGEAR", ["SWGR-SEA-01", "SWGR-SEA-02", "SWGR-ABB-01"]),
    ("CRAC_UNIT", ["CRAC-VRT-01", "CRAC-VRT-02", "CRAC-STO-01"]),
    ("CHILLER", ["CHI-TRN-01", "CHI-TRN-02", "CHI-CAR-01"]),
    ("COOLING_TOWER", ["CTW-BAL-01", "CTW-BAL-02"]),
    ("PDU", ["PDU-VER-01", "PDU-VER-02", "PDU-VER-03", "PDU-VER-04"]),
    ("BUSWAY", ["BUS-SIE-01", "BUS-SIE-02", "BUS-EAT-01"]),
    ("FIBER_SWITCH", ["FS-CIS-01", "FS-CIS-02", "FS-JUN-01"]),
    ("FIRE_PANEL", ["FP-HON-01", "FP-HON-02"]),
    ("ACCESS_FLOOR", ["AFL-TRU-01", "AFL-TRU-02", "AFL-TRU-03"]),
    ("CONTAINMENT", ["CONT-VRT-01", "CONT-PAN-01", "CONT-PAN-02"]),
    ("CABLE_TRAY", ["CT-USM-01", "CT-USM-02", "CT-USM-03"]),
    ("BMS_CONTROLLER", ["BMS-HON-01", "BMS-HON-02", "BMS-SIE-01"]),
]

VENDORS = {
    "GEN": "Caterpillar Inc.", "UPS": "Eaton Corporation", "XFMR": "ABB Ltd.",
    "SWGR": "Schneider Electric", "CRAC": "Vertiv Group", "CHI": "Trane Technologies",
    "CTW": "Baltimore Aircoil", "PDU": "Vertiv Group", "BUS": "Siemens AG",
    "FS": "Cisco Systems", "FP": "Honeywell", "AFL": "Tate Access Floors",
    "CONT": "Panduit Corp", "CT": "Unistrut", "BMS": "Honeywell",
}

STATUSES = ["On Track", "On Track", "On Track", "At Risk", "On Track", "On Track",
            "Confirmed", "Confirmed", "At Risk", "On Track"]


def generate_supply_chain(schedule_tasks: list[dict]) -> list[dict]:
    print("[2/3] Generating supply_chain.csv (50 items with forced GEN-CAT-01 conflict)...")
    items = []
    all_tags = [f"{cat[1][i]}" for cat in EQUIPMENT_CATEGORIES for i in range(len(cat[1]))][:50]

    # Find critical task linked to generator to map the conflict
    gen_critical_task = next(
        (t for t in schedule_tasks if "ELECTRICAL" in t["phase"] and t["is_critical"] == 1),
        schedule_tasks[0],
    )

    for i, tag in enumerate(all_tags):
        prefix = tag.split("-")[0]
        vendor = VENDORS.get(prefix, "Generic Supplier")
        lead_time = random.randint(60, 180)
        delay_days = 0
        status = random.choice(STATUSES)

        # FORCED CONFLICT: GEN-CAT-01 is in Customs Hold with 18-day delay
        if tag == "GEN-CAT-01":
            status = "Customs Hold"
            delay_days = 18
            lead_time = 120
            linked_task = gen_critical_task["task_id"]
        else:
            linked_task = random.choice(schedule_tasks)["task_id"] if random.random() < 0.4 else ""
            if status in ["At Risk", "Customs Hold"]:
                delay_days = random.randint(3, 12)

        items.append({
            "equipment_tag": tag,
            "description": f"{prefix} Equipment - {tag}",
            "vendor": vendor,
            "origin_country": random.choice(["USA", "Germany", "China", "Japan", "South Korea", "India"]),
            "lead_time_days": lead_time,
            "delay_days": delay_days,
            "status": status,
            "linked_task": linked_task,
            "unit_cost_usd": random.randint(10000, 2500000),
            "quantity": random.randint(1, 8),
            "port_of_entry": random.choice(["Los Angeles", "Newark", "Houston", "Seattle", "Chicago"]),
        })

    out_path = DATA_DIR / "supply_chain.csv"
    fieldnames = ["equipment_tag", "description", "vendor", "origin_country", "lead_time_days",
                  "delay_days", "status", "linked_task", "unit_cost_usd", "quantity", "port_of_entry"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)
    print(f"    [OK] Saved {len(items)} equipment items -> {out_path}")
    print(f"    [WARN] GEN-CAT-01 -> 'Customs Hold' / +18 days -> linked to {gen_critical_task['task_id']}")
    return items


# ---------------------------------------------------------------------------
# 3. RFI LOGS JSON
# ---------------------------------------------------------------------------
RFI_CATEGORIES = [
    "Structural Interference", "MEP Coordination Conflict", "Drawing Discrepancy",
    "Equipment Clearance Violation", "Specification Ambiguity", "Cable Routing Conflict",
    "Grounding System Gap", "Seismic Bracing Non-Compliance", "Conduit Routing Deviation",
    "Fire Rating Penetration Issue",
]

RFI_RESOLUTIONS = [
    "Revised drawing issued. Contractor to proceed per RFI response.",
    "Engineer of Record confirmed site condition. Proceed with field modification.",
    "Substitution approved. Submit product data for record.",
    "Request denied. Contractor to comply with contract documents.",
    "Partial approval. Resubmit revised shop drawing within 5 business days.",
    "Awaiting Structural Engineer review. Hold work pending response.",
    "Approved with condition: coordinate with MEP subcontractors prior to installation.",
]

LOCATIONS = [
    "Generator Room - Level B1", "Main MV Switchgear Room", "IT Hall A - Row 12",
    "IT Hall B - Row 8", "Cooling Plant - Rooftop Level", "Loading Dock - East",
    "Fiber Meet-Me Room", "Admin Block - Level 2", "UPS Room A", "UPS Room B",
    "CW Pipe Chase - Zone 3", "IT Hall C - Row 5",
]


def generate_rfi_logs() -> list[dict]:
    print("[3/3] Generating rfi_logs.json (50 engineering conflict logs)...")
    rfis = []
    for i in range(1, 51):
        rfi_id = f"RFI-{i:03d}"
        category = random.choice(RFI_CATEGORIES)
        location = random.choice(LOCATIONS)
        days_open = random.randint(1, 45)
        status = random.choice(["Open", "Open", "Resolved", "Resolved", "Pending Review"])
        resolution = random.choice(RFI_RESOLUTIONS) if status == "Resolved" else ""

        rfis.append({
            "rfi_id": rfi_id,
            "title": f"{category} at {location}",
            "category": category,
            "location": location,
            "submitted_by": random.choice(["J. Williams (Site Engr)", "K. Patel (MEP Lead)",
                                           "R. Chen (Structural)", "A. Kumar (Elec. Engr)",
                                           "S. Johnson (Mech Engr)", "T. Nguyen (QA Lead)"]),
            "date_submitted": f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "days_open": days_open,
            "status": status,
            "priority": random.choice(["Critical", "High", "Medium", "Low"]),
            "spec_reference": random.choice([
                "TIA-942-B Section 7.3.4", "ASHRAE 90.4-2019 Section 5.1", "NEC 2023 Article 700",
                "IEC 60364-7", "Uptime Tier III Section 4.1.2", "NFPA 75 Section 6.2",
                "IEEE 1100-2005 Section 8.4", "TIA-942-B Section 6.5.1",
            ]),
            "description": (
                f"During {random.choice(['installation', 'routing review', 'inspection', 'submittal review'])} "
                f"at {location}, a conflict was identified: {category.lower()} "
                f"that requires {'immediate' if days_open < 5 else 'expedited'} resolution. "
                f"The condition was first observed by {random.choice(['the field crew', 'the QA inspector', 'the MEP coordinator'])} "
                f"and impacts {random.choice(['schedule critical path', 'Phase 2 completion', 'electrical energization sequence', 'cooling plant startup'])}."
            ),
            "resolution_notes": resolution,
            "cost_impact_usd": random.choice([0, 0, 0, random.randint(5000, 250000)]),
            "schedule_impact_days": random.choice([0, 0, 0, random.randint(1, 15)]),
        })

    out_path = DATA_DIR / "rfi_logs.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rfis, f, indent=2)
    print(f"    [OK] Saved {len(rfis)} RFI logs -> {out_path}")
    return rfis


# ---------------------------------------------------------------------------
# 4. TIA-942 SPEC CHUNKS (for RAG index)
# ---------------------------------------------------------------------------
TIA942_SPEC_CHUNKS = [
    {
        "id": "TIA-942-7.3.4",
        "source": "TIA-942-B",
        "content": "Section 7.3.4 - Generator Systems: Standby generator systems shall be rated for continuous duty operation at site altitude and ambient temperature. Fuel storage shall support a minimum of 24 hours at full load for Tier III and 96 hours for Tier IV. Generator output voltage tolerance shall not exceed +/-5% of nominal. Transfer time from loss of utility to full generator output shall not exceed 10 seconds.",
        "metadata": {"section": "7.3.4", "tier": "III-IV", "topic": "generators"}
    },
    {
        "id": "TIA-942-7.2.1",
        "source": "TIA-942-B",
        "content": "Section 7.2.1 - UPS Systems: Uninterruptible Power Supply systems shall provide a minimum of 10 minutes runtime at full design load. Double-conversion topology is required for Tier III and above. Input voltage range shall accept 480V +/-10% three-phase. UPS output harmonic distortion (THDv) shall not exceed 5% at full linear load.",
        "metadata": {"section": "7.2.1", "tier": "III-IV", "topic": "ups"}
    },
    {
        "id": "TIA-942-6.5.1",
        "source": "TIA-942-B",
        "content": "Section 6.5.1 - Cable Pathways: All cable pathways shall be rated for the intended load. Minimum cable tray width shall be 300mm for power distribution. Separation between power and data cables shall be maintained at a minimum 300mm horizontal distance or 150mm with metal barrier. Cable fill shall not exceed 40% of tray cross-sectional area.",
        "metadata": {"section": "6.5.1", "tier": "I-IV", "topic": "cabling"}
    },
    {
        "id": "TIA-942-5.3.2",
        "source": "TIA-942-B",
        "content": "Section 5.3.2 - Cooling Systems: The design cooling capacity shall accommodate 110% of the IT load. CRAC unit redundancy shall comply with N+1 for Tier III. Supply air temperature at equipment inlet shall be maintained between 18degC and 27degC (ASHRAE A1 class). Humidity shall be controlled between 40% and 60% RH non-condensing.",
        "metadata": {"section": "5.3.2", "tier": "III", "topic": "cooling"}
    },
    {
        "id": "ASHRAE-90.4-5.1",
        "source": "ASHRAE 90.4-2019",
        "content": "Section 5.1 - Mechanical Load Component (MLC): The MLC shall not exceed 0.20 for all climate zones. Airside economizer shall be utilized where the climate allows free cooling for more than 1,200 hours per year. Power Usage Effectiveness (PUE) target for new construction shall be <=1.4 for Tier III equivalent facilities.",
        "metadata": {"section": "5.1", "standard": "ASHRAE 90.4-2019", "topic": "energy_efficiency"}
    },
    {
        "id": "UPTIME-TIER3-4.1.2",
        "source": "Uptime Institute Tier Standard",
        "content": "Tier III Concurrently Maintainable - Section 4.1.2: All capacity and distribution components must be concurrently maintainable. Site infrastructure must be capable of undergoing planned maintenance activities while supporting the critical environment. Redundant distribution paths N+1 are required. Annual site downtime shall not exceed 1.6 hours (99.982% availability).",
        "metadata": {"tier": "III", "standard": "Uptime Institute", "topic": "availability"}
    },
    {
        "id": "TIA-942-7.4.3",
        "source": "TIA-942-B",
        "content": "Section 7.4.3 - Grounding and Bonding: All data center equipment shall be bonded to a single point ground (SPG) reference. The grounding electrode system shall achieve a resistance of <=1 ohm to earth. Signal Reference Grid (SRG) shall be installed in raised floor installations. Equipotential bonding conductors shall be minimum 6 AWG copper.",
        "metadata": {"section": "7.4.3", "tier": "I-IV", "topic": "grounding"}
    },
    {
        "id": "NFPA-75-6.2",
        "source": "NFPA 75",
        "content": "Section 6.2 - Fire Suppression: Computer rooms housing IT equipment shall be protected by an automatic sprinkler system or a clean agent suppression system. Clean agent systems shall comply with NFPA 2001. Pre-action sprinkler systems are permitted as an alternative. Detection systems shall include both smoke and heat detection with cross-zoning.",
        "metadata": {"section": "6.2", "standard": "NFPA 75", "topic": "fire_suppression"}
    },
]


def generate_spec_chunks():
    """Save spec chunks as JSON for indexing."""
    out_path = DATA_DIR / "spec_chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(TIA942_SPEC_CHUNKS, f, indent=2)
    print(f"    [OK] Saved {len(TIA942_SPEC_CHUNKS)} TIA-942/ASHRAE spec chunks -> {out_path}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  AURA-EPC Data Hydration Script")
    print("=" * 60)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "models").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "vector_index").mkdir(parents=True, exist_ok=True)

    schedule_tasks = generate_master_schedule()
    supply_items = generate_supply_chain(schedule_tasks)
    rfi_logs = generate_rfi_logs()
    generate_spec_chunks()

    print("\n" + "=" * 60)
    print("  Data hydration complete!")
    print(f"  Schedule tasks : {len(schedule_tasks)}")
    print(f"  Supply items   : {len(supply_items)}")
    print(f"  RFI logs       : {len(rfi_logs)}")
    print("  [WARN] GEN-CAT-01 is in CUSTOMS HOLD (+18 days delay)")
    print("=" * 60)

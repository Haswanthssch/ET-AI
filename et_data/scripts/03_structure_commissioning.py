"""
Step 3: Structure Commissioning PDFs into pass/fail step JSON.

Outputs per PDF:
  - {stem}.commissioning.json   -> structured procedure as nested JSON
  - {stem}.commissioning.md     -> human-readable markdown w/ tables + steps

Procedure detection:
  - Section headers: numbered (1., 1.1, 5.2.1) or ALL-CAPS lines
  - Steps: (1), (a), Step 1:, numbered lists
  - Pass/fail keywords: PASS, FAIL, ACCEPT, REJECT, COMPLIANT, NON-COMPLIANT,
    YES/NO, OK/NOK, "verify", "confirm", "check", "shall", "must"
"""

import re
import json
from pathlib import Path
from datetime import datetime

RAW_TEXT_DIR = Path(r"c:\Users\haswa.HASWANTH\Downloads\et_data\preprocessed\01_raw_text")
STRUCTURED_DIR = Path(r"c:\Users\haswa.HASWANTH\Downloads\et_data\preprocessed\02_structured_json")
OUTPUT_DIR = Path(r"c:\Users\haswa.HASWANTH\Downloads\et_data\preprocessed\04_commissioning_json")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COMMISSIONING_FILES = [
    "eaton-93t-ups-commissioning-instructions-en-us.txt",
    "uninterruptible-power-supply-battery-acceptance-capacity-test-procedure.txt",
]

SECTION_HEADING = re.compile(
    r"^(?:"
    r"\d+(?:\.\d+){0,3}\s+[A-Z][^\n]{2,140}"   # 5.2.1 Heading
    r"|[A-Z][A-Z0-9 \-/&,()]{4,80}"            # ALL CAPS
    r")$"
)

STEP_PATTERN = re.compile(
    r"^(?:"
    r"\(\s*(?P<num1>\d{1,3}|[a-zA-Z])\s*\)"    # (1) (a)
    r"|Step\s+(?P<num2>\d{1,3})[\.\:]"          # Step 1:
    r"|(?P<num3>\d{1,3})[\.\)]\s+"              # 1. or 1)
    r")",
    re.IGNORECASE,
)

PASS_FAIL_KEYWORDS = [
    "pass", "fail", "accept", "reject", "compliant", "non-compliant",
    "yes/no", "ok/nok", "satisfactory", "unsatisfactory",
]
VERIFY_KEYWORDS = ["verify", "confirm", "check", "ensure", "measure", "record", "shall", "must"]


def has_pass_fail_signal(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in PASS_FAIL_KEYWORDS)


def has_verify_signal(text: str) -> bool:
    low = text.lower()
    return any(re.search(rf"\b{k}\b", low) for k in VERIFY_KEYWORDS)


def classify_step(text: str) -> str:
    if has_pass_fail_signal(text):
        return "pass_fail_check"
    if has_verify_signal(text):
        return "verification"
    return "action"


def extract_steps_from_section(body: str) -> list[dict]:
    """Detect numbered/bulleted procedural steps within a section body."""
    lines = body.split("\n")
    steps = []
    current_step = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        m = STEP_PATTERN.match(stripped)
        if m:
            if current_step:
                current_step["text"] = re.sub(r"\s+", " ", current_step["text"]).strip()
                current_step["type"] = classify_step(current_step["text"])
                current_step["pass_fail_gate"] = has_pass_fail_signal(current_step["text"])
                if current_step["text"]:
                    steps.append(current_step)
            num = m.group("num1") or m.group("num2") or m.group("num3") or ""
            current_step = {
                "step_id": num,
                "text": stripped[m.end():].strip(),
                "type": "action",
                "pass_fail_gate": False,
            }
        else:
            if current_step is None:
                continue
            current_step["text"] += " " + stripped

    if current_step:
        current_step["text"] = re.sub(r"\s+", " ", current_step["text"]).strip()
        current_step["type"] = classify_step(current_step["text"])
        current_step["pass_fail_gate"] = has_pass_fail_signal(current_step["text"])
        if current_step["text"]:
            steps.append(current_step)
    return steps


def split_sections(text: str) -> list[dict]:
    lines = text.split("\n")
    sections = []
    current = {"heading": "Preamble", "body_lines": []}
    for line in lines:
        stripped = line.strip()
        if SECTION_HEADING.match(stripped) and len(stripped) > 4:
            if current["body_lines"]:
                body = "\n".join(current["body_lines"]).strip()
                current["body"] = body
                current["steps"] = extract_steps_from_section(body)
                del current["body_lines"]
                if body:
                    sections.append(current)
            current = {"heading": stripped, "body_lines": []}
        else:
            current["body_lines"].append(line)
    if current.get("body_lines"):
        body = "\n".join(current["body_lines"]).strip()
        current["body"] = body
        current["steps"] = extract_steps_from_section(body)
        del current["body_lines"]
        if body:
            sections.append(current)
    return sections


def load_metadata_and_tables(stem: str) -> dict:
    """Pull tables + page metadata from step 1's structured JSON."""
    json_path = STRUCTURED_DIR / f"{stem}.json"
    if not json_path.exists():
        return {"tables": [], "metadata": {}, "original_filename": "", "source_file": ""}
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Filter out near-empty tables (most cells blank)
    real_tables = []
    for t in data.get("tables", []):
        non_empty_cells = sum(1 for row in t.get("raw", []) for c in row if c and c.strip())
        total_cells = sum(len(row) for row in t.get("raw", []))
        if total_cells > 0 and non_empty_cells / total_cells > 0.3:
            real_tables.append(t)
    return {
        "tables": real_tables,
        "metadata": data.get("metadata", {}),
        "original_filename": data.get("filename", ""),
        "source_file": data.get("source_file", ""),
    }


def build_markdown(doc: dict) -> str:
    md = [f"# {doc['title']}", "", f"_Source: `{doc['original_filename']}`_  ",
          f"_Pages: {doc['page_count']} | Sections: {doc['section_count']} | "
          f"Steps: {doc['total_steps']} | Pass/Fail gates: {doc['pass_fail_gate_count']}_", ""]
    for sec in doc["sections"]:
        md.append(f"## {sec['heading']}")
        md.append("")
        if sec["steps"]:
            for s in sec["steps"]:
                gate = "  **[PASS/FAIL GATE]**" if s["pass_fail_gate"] else ""
                md.append(f"- **Step {s['step_id'] or '-'}** ({s['type']}){gate}: {s['text']}")
        else:
            # Trim long body to ~600 chars in markdown for readability
            body = re.sub(r"\s+", " ", sec["body"]).strip()
            md.append(body[:1200] + ("..." if len(body) > 1200 else ""))
        md.append("")
    if doc.get("tables"):
        md.append("## Extracted Tables")
        md.append("")
        for t in doc["tables"]:
            md.append(f"### Page {t['page']} — Table {t['table_index']}")
            md.append("")
            md.append(t["markdown"])
            md.append("")
    return "\n".join(md)


def main():
    results = []
    for fname in COMMISSIONING_FILES:
        path = RAW_TEXT_DIR / fname
        if not path.exists():
            print(f"MISSING: {fname}")
            continue
        text = path.read_text(encoding="utf-8")
        sections = split_sections(text)
        meta = load_metadata_and_tables(path.stem)

        total_steps = sum(len(s["steps"]) for s in sections)
        pass_fail_gates = sum(
            1 for s in sections for st in s["steps"] if st["pass_fail_gate"]
        )

        # Title: first non-empty line of meaningful length
        title_lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        title = next((ln for ln in title_lines if 8 < len(ln) < 140), path.stem)

        doc = {
            "source_file": fname,
            "original_filename": meta["original_filename"],
            "original_source_path": meta["source_file"],
            "title": title,
            "document_type": "Commissioning_Procedure",
            "category": "Commissioning/UPS",
            "page_count": meta["metadata"].get("page_count", 0),
            "section_count": len(sections),
            "total_steps": total_steps,
            "pass_fail_gate_count": pass_fail_gates,
            "table_count": len(meta["tables"]),
            "sections": sections,
            "tables": meta["tables"],
            "structured_at": datetime.now().isoformat(),
            "extraction_method": "regex sectioning + step-pattern + pass/fail keyword classification",
            "extraction_notes": (
                "Auto-extracted. For production use, manually review and validate "
                "pass/fail gates and step ordering against the source PDF."
            ),
        }

        out_json = OUTPUT_DIR / f"{path.stem}.commissioning.json"
        out_md = OUTPUT_DIR / f"{path.stem}.commissioning.md"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        out_md.write_text(build_markdown(doc), encoding="utf-8")

        results.append({
            "file": fname,
            "title": title,
            "pages": doc["page_count"],
            "sections": len(sections),
            "steps": total_steps,
            "pass_fail_gates": pass_fail_gates,
            "tables": len(meta["tables"]),
        })
        print(f"  {fname}: sections={len(sections)} steps={total_steps} "
              f"pass/fail={pass_fail_gates} tables={len(meta['tables'])}")

    summary = OUTPUT_DIR / "_commissioning_summary.json"
    with open(summary, "w", encoding="utf-8") as f:
        json.dump({"total_documents": len(results), "documents": results}, f, ensure_ascii=False, indent=2)

    print("\n=== COMMISSIONING STRUCTURING SUMMARY ===")
    print(f"Documents:       {len(results)}")
    print(f"Total steps:     {sum(r['steps'] for r in results)}")
    print(f"Pass/fail gates: {sum(r['pass_fail_gates'] for r in results)}")
    print(f"Output dir:      {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

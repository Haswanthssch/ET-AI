"""
Step 2: Structure RFI documents into Q&A JSON.

Detects patterns like:
  Q1: / Q1.  ... A1: / A1.
  Q-1) / A-1)
  Question 1: ... Answer 1:

Output: one JSON file per RFI with:
  {
    "source_file": ...,
    "rfi_id": ...,
    "title": ...,
    "qa_pairs": [
      { "id": 1, "question": "...", "answer": "..." }, ...
    ],
    "metadata": {...}
  }
"""

import re
import json
from pathlib import Path
from datetime import datetime

RAW_TEXT_DIR = Path(r"c:\Users\haswa.HASWANTH\Downloads\et_data\preprocessed\01_raw_text")
STRUCTURED_DIR = Path(r"c:\Users\haswa.HASWANTH\Downloads\et_data\preprocessed\02_structured_json")
OUTPUT_DIR = Path(r"c:\Users\haswa.HASWANTH\Downloads\et_data\preprocessed\03_rfi_qa_json")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# RFI files (from datasets/04_Project_Communications/RFIs/)
RFI_FILES = [
    "Data_Center_RFI_Response_-_Geothermal_Rising.txt",
    "Grid-Action-Data-Center-RFI-Response-05-07-25.txt",
    "Impact_Control_of_RFIs_on_Construction_Projects.txt",
    "Questions_and_Answers_3.txt",
    "RFI_10887-25_Questions_and_Answers_12.1.25.txt",
    "RFI_10887-25_Questions_and_Answers_12.8.25.txt",
    "rfi_for_cloud_adoption.txt",
    "RFI_to_Inform_Public_Bids_to_Construct_AI_Infrastructure_website_copy_.txt",
    "RFI-Template-for-PCI-3.0.txt",
    "RFI_.txt",
    "rfi_quick_reference_guide.txt",
    "SIIA-RFI-Response-_-Accelerating-Speed-to-Power.txt",
    "TR-524_RFI_Template_for_Migration_to__SDN.txt",
]

# Patterns: capture question/answer markers
# Handles: Q1:, Q1., Q1), Q-1:, Q.#1:, Question 1:, Q #1:
Q_PATTERN = re.compile(
    r"(?:^|\n)[ \t]*"
    r"(?:Q(?:uestion)?[\s\-\.#]*)"
    r"(?P<num>\d{1,3})"
    r"[\.\:\)]"
    r"[ \t]+",
    re.IGNORECASE | re.MULTILINE,
)
A_PATTERN = re.compile(
    r"(?:^|\n)[ \t]*"
    r"(?:A(?:nswer)?[\s\-\.#]*)"
    r"(?P<num>\d{1,3})?"  # number optional (some docs use bare "A:")
    r"[\.\:\)]"
    r"[ \t]+",
    re.IGNORECASE | re.MULTILINE,
)


def extract_qa_pairs(text: str) -> list[dict]:
    """Find all Q#/A# pairs by their offsets in the text."""
    q_matches = list(Q_PATTERN.finditer(text))
    a_matches = list(A_PATTERN.finditer(text))

    if not q_matches:
        return []

    # Build markers list and sort
    markers = []
    for m in q_matches:
        markers.append({"kind": "Q", "num": int(m.group("num")), "start": m.start(), "end": m.end()})
    for m in a_matches:
        num_str = m.group("num")
        markers.append({"kind": "A", "num": int(num_str) if num_str else None, "start": m.start(), "end": m.end()})
    markers.sort(key=lambda x: x["start"])

    pairs: dict[int, dict] = {}
    last_q_num = 0
    for i, marker in enumerate(markers):
        next_start = markers[i + 1]["start"] if i + 1 < len(markers) else len(text)
        body = text[marker["end"]:next_start].strip()
        body = re.sub(r"\s+", " ", body)
        num = marker["num"]
        if marker["kind"] == "Q":
            last_q_num = num if num else last_q_num + 1
            key = last_q_num
        else:
            # Bare "A:" -> attach to most recent question number
            key = num if num else last_q_num
        if key not in pairs:
            pairs[key] = {"id": key, "question": "", "answer": ""}
        if marker["kind"] == "Q" and not pairs[key]["question"]:
            pairs[key]["question"] = body
        elif marker["kind"] == "A" and not pairs[key]["answer"]:
            pairs[key]["answer"] = body

    return [p for _, p in sorted(pairs.items()) if p["question"] or p["answer"]]


def extract_rfi_id_and_title(text: str, filename: str) -> tuple[str, str]:
    """Try to detect RFI ID and title from the first ~500 chars."""
    head = text[:800]
    rfi_id_match = re.search(r"RFI[\s\-]*(?:No\.?|#)?\s*([A-Z0-9][\w\-/]{2,30})", head, re.IGNORECASE)
    rfi_id = rfi_id_match.group(1).strip() if rfi_id_match else filename.replace(".txt", "")
    # Title: take the first non-empty line of meaningful length
    lines = [ln.strip() for ln in head.split("\n") if ln.strip()]
    title = ""
    for ln in lines[:6]:
        if 10 < len(ln) < 140 and not re.match(r"^Q\d", ln, re.IGNORECASE):
            title = ln
            break
    return rfi_id, title


def load_structured_metadata(filename_stem: str) -> dict:
    """Pull page count + source path from the structured JSON written by step 1."""
    json_path = STRUCTURED_DIR / f"{filename_stem}.json"
    if not json_path.exists():
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "page_count": data.get("metadata", {}).get("page_count", 0),
            "original_source": data.get("source_file", ""),
            "original_filename": data.get("filename", ""),
        }
    except Exception:
        return {}


def split_into_sections(text: str) -> list[dict]:
    """Best-effort section split for narrative RFI documents (no Q&A pairs).

    Detects ALL-CAPS headings or numbered headings (1., 2.1, etc.).
    """
    lines = text.split("\n")
    sections = []
    current = {"heading": "Introduction", "body_lines": []}

    heading_pat = re.compile(
        r"^(?:"
        r"[A-Z][A-Z0-9 \-/&,()]{4,80}"            # ALL CAPS
        r"|\d+(?:\.\d+)*[\.\)]\s+[A-Z][^\n]{3,120}"  # 1. Title or 2.1 Title
        r")$"
    )
    for line in lines:
        stripped = line.strip()
        if heading_pat.match(stripped):
            if current["body_lines"]:
                current["body"] = re.sub(r"\s+", " ", " ".join(current["body_lines"])).strip()
                del current["body_lines"]
                if current["body"]:
                    sections.append(current)
            current = {"heading": stripped, "body_lines": []}
        else:
            current["body_lines"].append(stripped)

    if current.get("body_lines"):
        current["body"] = re.sub(r"\s+", " ", " ".join(current["body_lines"])).strip()
        del current["body_lines"]
        if current["body"]:
            sections.append(current)

    return sections


def main():
    results = []
    for fname in RFI_FILES:
        path = RAW_TEXT_DIR / fname
        if not path.exists():
            print(f"MISSING: {fname}")
            continue

        text = path.read_text(encoding="utf-8")
        qa_pairs = extract_qa_pairs(text)
        rfi_id, title = extract_rfi_id_and_title(text, fname)
        meta = load_structured_metadata(path.stem)

        doc_subtype = "qa_document" if qa_pairs else "narrative_document"
        sections = [] if qa_pairs else split_into_sections(text)

        output = {
            "source_file": fname,
            "original_filename": meta.get("original_filename", ""),
            "original_source_path": meta.get("original_source", ""),
            "rfi_id": rfi_id,
            "title": title,
            "document_type": "RFI",
            "document_subtype": doc_subtype,
            "category": "Project_Communications/RFIs",
            "page_count": meta.get("page_count", 0),
            "char_count": len(text),
            "qa_pair_count": len(qa_pairs),
            "qa_pairs": qa_pairs,
            "section_count": len(sections),
            "sections": sections,
            "structured_at": datetime.now().isoformat(),
            "extraction_method": "regex Q#/A# pattern matching + heading-based sectioning",
        }

        out_path = OUTPUT_DIR / f"{path.stem}.qa.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        results.append({
            "file": fname,
            "rfi_id": rfi_id,
            "subtype": doc_subtype,
            "qa_pairs": len(qa_pairs),
            "sections": len(sections),
        })
        print(f"  {fname}: subtype={doc_subtype}, Q&A={len(qa_pairs)}, sections={len(sections)}")

    # Summary
    summary_path = OUTPUT_DIR / "_rfi_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_rfis": len(results),
            "total_qa_pairs": sum(r["qa_pairs"] for r in results),
            "qa_documents": sum(1 for r in results if r["subtype"] == "qa_document"),
            "narrative_documents": sum(1 for r in results if r["subtype"] == "narrative_document"),
            "rfis": results,
        }, f, ensure_ascii=False, indent=2)

    print("\n=== RFI STRUCTURING SUMMARY ===")
    print(f"RFIs processed:       {len(results)}")
    print(f"Q&A documents:        {sum(1 for r in results if r['subtype'] == 'qa_document')}")
    print(f"Narrative documents:  {sum(1 for r in results if r['subtype'] == 'narrative_document')}")
    print(f"Total Q&A pairs:      {sum(r['qa_pairs'] for r in results)}")
    print(f"Output dir:           {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

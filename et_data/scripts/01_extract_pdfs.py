"""
Step 1: PDF Text Extraction
- Uses PyMuPDF (fitz) for general text + metadata
- Uses pdfplumber for tables
- Strips headers/footers, normalizes whitespace
- Outputs: per-PDF .txt (clean) + per-PDF .json (structured w/ pages + tables)
"""

import os
import re
import json
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from datetime import datetime

DATASETS_DIR = Path(r"c:\Users\haswa.HASWANTH\Downloads\et_data\datasets")
OUTPUT_DIR = Path(r"c:\Users\haswa.HASWANTH\Downloads\et_data\preprocessed")
RAW_TEXT_DIR = OUTPUT_DIR / "01_raw_text"
STRUCTURED_DIR = OUTPUT_DIR / "02_structured_json"

# Skip pdfplumber table extraction for PDFs above this size (too slow for huge manuals)
MAX_TABLE_EXTRACTION_MB = 5

RAW_TEXT_DIR.mkdir(parents=True, exist_ok=True)
STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    """Remove noise: extra whitespace, page numbers, repeated headers."""
    if not text:
        return ""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove standalone page-number lines like "Page 3 of 12" or "- 3 -"
    text = re.sub(r"^\s*(page\s+)?\d+(\s+of\s+\d+)?\s*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"^\s*-\s*\d+\s*-\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


def detect_repeated_headers_footers(pages_text: list[str]) -> set[str]:
    """Find lines that appear on >50% of pages (likely headers/footers)."""
    if len(pages_text) < 3:
        return set()
    line_counts: dict[str, int] = {}
    for page in pages_text:
        seen = set()
        for line in page.split("\n"):
            stripped = line.strip()
            if 3 < len(stripped) < 120 and stripped not in seen:
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
                seen.add(stripped)
    threshold = max(2, len(pages_text) // 2)
    return {line for line, count in line_counts.items() if count >= threshold}


def remove_headers_footers(page_text: str, noise_lines: set[str]) -> str:
    if not noise_lines:
        return page_text
    return "\n".join(line for line in page_text.split("\n") if line.strip() not in noise_lines)


def extract_tables_with_pdfplumber(pdf_path: Path) -> list[dict]:
    """Extract tables and convert to markdown format."""
    tables_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for tbl_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    md = table_to_markdown(table)
                    tables_data.append({
                        "page": page_num,
                        "table_index": tbl_idx,
                        "rows": len(table),
                        "cols": len(table[0]) if table[0] else 0,
                        "markdown": md,
                        "raw": table,
                    })
    except Exception as e:
        print(f"  [tables] warning on {pdf_path.name}: {e}")
    return tables_data


def table_to_markdown(table: list[list]) -> str:
    if not table:
        return ""
    cleaned = [[(cell if cell is not None else "").strip().replace("\n", " ") for cell in row] for row in table]
    header = cleaned[0]
    body = cleaned[1:]
    md_lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in body:
        # pad missing cells
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        md_lines.append("| " + " | ".join(row[: len(header)]) + " |")
    return "\n".join(md_lines)


def extract_pdf(pdf_path: Path) -> dict:
    """Extract text + metadata + tables from a single PDF."""
    result = {
        "source_file": str(pdf_path),
        "filename": pdf_path.name,
        "category": pdf_path.parent.name,
        "parent_category": pdf_path.parent.parent.name if pdf_path.parent.parent != DATASETS_DIR else pdf_path.parent.name,
        "extracted_at": datetime.now().isoformat(),
        "pages": [],
        "tables": [],
        "metadata": {},
        "full_text": "",
        "errors": [],
    }

    # 1) PyMuPDF for text + doc metadata
    try:
        doc = fitz.open(pdf_path)
        result["metadata"] = {
            "page_count": doc.page_count,
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
        }
        raw_pages = [page.get_text("text") for page in doc]
        doc.close()
    except Exception as e:
        result["errors"].append(f"PyMuPDF failed: {e}")
        return result

    noise = detect_repeated_headers_footers(raw_pages)
    cleaned_pages = []
    for i, page_text in enumerate(raw_pages, start=1):
        stripped = remove_headers_footers(page_text, noise)
        cleaned = clean_text(stripped)
        cleaned_pages.append({"page": i, "text": cleaned, "char_count": len(cleaned)})

    result["pages"] = cleaned_pages
    result["full_text"] = "\n\n".join(p["text"] for p in cleaned_pages if p["text"])
    result["removed_noise_lines"] = sorted(noise)

    # 2) pdfplumber for tables (skip very large PDFs to keep runtime reasonable)
    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    if size_mb <= MAX_TABLE_EXTRACTION_MB:
        result["tables"] = extract_tables_with_pdfplumber(pdf_path)
    else:
        result["tables"] = []
        result["errors"].append(f"Table extraction skipped (size {size_mb:.1f} MB > {MAX_TABLE_EXTRACTION_MB} MB)")

    return result


def find_all_pdfs() -> list[Path]:
    pdfs = []
    for path in DATASETS_DIR.rglob("*.pdf"):
        # skip 15_Web_Assets / 14_Unclassified? -> include all
        pdfs.append(path)
    return sorted(pdfs)


def main():
    pdfs = find_all_pdfs()
    print(f"Found {len(pdfs)} PDFs")
    summary = []

    for i, pdf_path in enumerate(pdfs, start=1):
        rel = pdf_path.relative_to(DATASETS_DIR)
        print(f"[{i}/{len(pdfs)}] {rel}")
        try:
            data = extract_pdf(pdf_path)
        except Exception as e:
            print(f"  FAILED: {e}")
            summary.append({"file": str(rel), "status": "failed", "error": str(e)})
            continue

        # safe filename
        safe_name = re.sub(r"[^\w\-.]+", "_", pdf_path.stem)

        # write raw text
        txt_path = RAW_TEXT_DIR / f"{safe_name}.txt"
        txt_path.write_text(data["full_text"], encoding="utf-8")

        # write structured JSON
        json_path = STRUCTURED_DIR / f"{safe_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        summary.append({
            "file": str(rel),
            "pages": data["metadata"].get("page_count", 0),
            "chars": len(data["full_text"]),
            "tables": len(data["tables"]),
            "status": "ok" if not data["errors"] else "partial",
            "errors": data["errors"],
        })

    # save extraction summary
    summary_path = OUTPUT_DIR / "extraction_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    total_chars = sum(s.get("chars", 0) for s in summary)
    total_tables = sum(s.get("tables", 0) for s in summary)
    failed = [s for s in summary if s["status"] == "failed"]
    print("\n=== EXTRACTION SUMMARY ===")
    print(f"Total PDFs:     {len(pdfs)}")
    print(f"Successful:     {len(pdfs) - len(failed)}")
    print(f"Failed:         {len(failed)}")
    print(f"Total chars:    {total_chars:,}")
    print(f"Total tables:   {total_tables}")
    print(f"Summary file:   {summary_path}")


if __name__ == "__main__":
    main()

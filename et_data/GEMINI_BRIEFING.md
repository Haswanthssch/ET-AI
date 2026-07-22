# Gemini Update — Stage 1 Preprocessing Complete

Paste the block below into Gemini to confirm Stage 1 and ask for Stage 2 guidance.

---

## What's done (Stage 1)

I implemented the local-first pipeline you suggested. No API keys used yet.

**Tooling**
- PyMuPDF (`pymupdf` 1.28) for text + metadata
- `pdfplumber` 0.11 for tables
- Header/footer noise stripped (lines appearing on >50% of pages)
- Whitespace normalized

**Outputs (under `preprocessed/`)**
- `01_raw_text/` — 36 cleaned `.txt` files (1,254,318 chars total)
- `02_structured_json/` — 36 per-PDF JSON with `pages`, `tables` (markdown + raw), `metadata`
- `03_rfi_qa_json/` — 13 RFI JSON files (Q&A pairs OR narrative sections)
- `04_commissioning_json/` — 2 commissioning JSON + markdown files

**Numbers**
- PDFs processed: 36 / 36, 0 failures
- Tables captured: 476
- RFI Q&A pairs: **137** (across 4 Q&A-format RFIs)
- RFIs in narrative format: 9
- Commissioning steps: **26**, with **9 pass/fail gates** (battery acceptance procedure)
- Eaton 93T commissioning slide deck: text fragmented (graphical bullets) — 5 tables captured but 0 steps

**RFI Q&A schema**
```json
{
  "rfi_id": "10887-25",
  "document_type": "RFI",
  "document_subtype": "qa_document",
  "qa_pair_count": 81,
  "qa_pairs": [
    { "id": 1, "question": "...", "answer": "..." }
  ]
}
```

**Commissioning schema**
```json
{
  "document_type": "Commissioning_Procedure",
  "sections": [{
    "heading": "INITIAL CONDITIONS",
    "steps": [
      { "step_id": "9", "text": "Measure and record all cell voltages...",
        "type": "pass_fail_check", "pass_fail_gate": true }
    ]
  }]
}
```

## Known gaps before Stage 2

1. **Eaton 93T slide deck** — PyMuPDF doesn't linearize bulleted slide graphics. This is the strongest candidate for LlamaParse OR OCR.
2. **No OCR** wired up yet — if any page is scanned, it extracts as empty.
3. **Pass/fail classification is keyword heuristic** — will need a sanity pass.
4. **No chunking, embedding, or vector DB** yet.

## What I need from you for Stage 2

Concrete, in this order:

1. **Chunking** — given 137 Q&A pairs + 26 procedural steps + ~1.25M chars of narrative text, what's the exact chunking strategy?
   - Should Q&A pairs stay as single chunks (regardless of length)?
   - Should each commissioning step be its own chunk?
   - Or roll multiple steps per section into 512–1024 token chunks?
2. **Metadata schema** — exact field list and types for each chunk in Qdrant. You mentioned `Document_Type`, `Discipline`, `Equipment_Tag`, `Date`. Anything else? How do I derive `Discipline` (Electrical/Mechanical/MEP) — keyword rules or LLM tagging?
3. **BGE-M3 deployment** — local Sentence-Transformers vs. running it via an inference server (e.g., TEI). Memory footprint and speed expectations on a typical dev laptop (no GPU)?
4. **Qdrant setup** — Docker single-node, or do you recommend Qdrant Cloud free tier for this volume? Index params (HNSW m, ef_construct, distance metric)?
5. **Re-processing the Eaton 93T deck** — go local OCR (Tesseract) first, or jump straight to LlamaParse for that single document?

Give me a concrete plan with the script structure for Stage 2 (chunker → embedder → uploader), please.

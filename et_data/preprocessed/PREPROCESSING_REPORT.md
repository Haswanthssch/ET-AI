# Preprocessing Report — Stage 1

**Project:** AI Intelligence Platform for Data Centre EPC Project Delivery
**Stage:** Text extraction + structured JSON for RFIs and Commissioning
**Generated:** 2026-06-29

---

## What Was Done

Implemented the Step-1 pipeline from the Gemini brief on a local Windows / Python 3.11 environment, with no external API keys.

1. **PDF text extraction** for all 36 organized PDFs
   - Engine: PyMuPDF (`pymupdf` 1.28) for text + document metadata
   - Tables: `pdfplumber` 0.11 (with a 5 MB size guard to keep runtime sane)
   - Header/footer noise stripped automatically (lines appearing on >50% of pages)
   - Output: cleaned `.txt` per PDF + structured `.json` per PDF (pages, tables, metadata)

2. **RFI Q&A structuring** for 13 RFI PDFs
   - Regex pattern matching for `Q1:` / `A1:`, `Q.#1:` / `A:`, `Q1.` / `A1.`, etc.
   - Documents without Q&A patterns are saved as `narrative_document` with section splits
   - Output: one `.qa.json` per RFI + a roll-up `_rfi_summary.json`

3. **Commissioning procedure structuring** for 2 Commissioning PDFs
   - Sections detected via ALL-CAPS / numbered heading regex
   - Steps detected via `(N)`, `(a)`, `Step N:`, `N.` patterns
   - Each step classified as **action**, **verification**, or **pass_fail_check** using keyword heuristics
   - Output: one `.commissioning.json` + one `.commissioning.md` per PDF

---

## Output Layout

```
preprocessed/
├── 01_raw_text/                 # 36 cleaned .txt files (1.25 M chars total)
├── 02_structured_json/          # 36 .json files with pages + tables + metadata
├── 03_rfi_qa_json/              # 13 RFI .qa.json + _rfi_summary.json
├── 04_commissioning_json/       # 2 .commissioning.json + .commissioning.md
│                                # + _commissioning_summary.json
├── extraction_summary.json      # roll-up of step 1
└── extraction_log.txt           # raw run log
```

---

## Numbers

### Text extraction (`01_raw_text`, `02_structured_json`)

| Metric | Value |
|---|---|
| PDFs processed | **36 / 36** |
| Failures | **0** |
| Total characters extracted | **1,254,318** |
| Total tables extracted | **476** |
| PDFs skipped for table extraction (>5 MB) | 4 (large equipment manuals) |

### RFI structuring (`03_rfi_qa_json`)

| Metric | Value |
|---|---|
| RFI PDFs processed | 13 |
| RFIs in **Q&A format** | 4 |
| RFIs in **narrative format** | 9 |
| Total Q&A pairs extracted | **137** |
| RFIs with the most Q&A pairs | `RFI 10887-25 12.8.25` (81), `Questions_and_Answers_3` (40), `RFI 10887-25 12.1.25` (9), `Geothermal_Rising` (7) |

### Commissioning structuring (`04_commissioning_json`)

| Document | Sections | Steps | Pass/Fail Gates | Tables |
|---|---|---|---|---|
| `uninterruptible-power-supply-battery-acceptance-capacity-test-procedure` | 2 | 26 | **9** | 0 |
| `eaton-93t-ups-commissioning-instructions-en-us` | 3 | 0 | 0 | 5 |

> The Eaton 93T PDF is a slide deck — its body text is rendered as graphical bullets that PyMuPDF cannot reliably linearize. The 5 usable tables were captured, but step extraction is empty. This PDF is the strongest candidate for **LlamaParse** or **OCR re-processing** in stage 2.

---

## Schema Examples

### RFI `*.qa.json` (Q&A document)

```json
{
  "source_file": "RFI_10887-25_Questions_and_Answers_12.8.25.txt",
  "rfi_id": "10887-25",
  "title": "RFI 10887-25",
  "document_type": "RFI",
  "document_subtype": "qa_document",
  "category": "Project_Communications/RFIs",
  "page_count": 14,
  "qa_pair_count": 81,
  "qa_pairs": [
    { "id": 1, "question": "Can companies from Outside USA apply for this?", "answer": "There is no limitation..." }
  ]
}
```

### Commissioning `*.commissioning.json`

```json
{
  "source_file": "uninterruptible-power-supply-battery-acceptance-capacity-test-procedure.txt",
  "title": "UNINTERRUPTIBLE POWER SUPPLY BATTERY ACCEPTANCE/CAPACITY TEST PROCEDURE",
  "document_type": "Commissioning_Procedure",
  "page_count": 9,
  "section_count": 2,
  "total_steps": 26,
  "pass_fail_gate_count": 9,
  "sections": [
    {
      "heading": "INITIAL CONDITIONS",
      "steps": [
        {
          "step_id": "3",
          "text": "Insure that all intercell connection resistances are under...",
          "type": "verification",
          "pass_fail_gate": false
        },
        {
          "step_id": "9",
          "text": "Measure and record all cell voltages and specific gravities...",
          "type": "pass_fail_check",
          "pass_fail_gate": true
        }
      ]
    }
  ]
}
```

---

## Known Limitations of Stage 1

1. **Slide-deck PDFs** (Eaton 93T) — PyMuPDF cannot linearize bulleted slide content. Tables come through but step text doesn't.
2. **Image-only / scanned content** — no OCR is wired up yet. If any RFI page is a scanned form, it currently extracts as empty.
3. **Pass/fail classification is heuristic** — based on keyword presence. False positives/negatives are expected.
4. **Section detection is conservative** — narrative RFIs without clear ALL-CAPS or numbered headings produce 1 large section.
5. **Vendor / equipment / discipline tags are not yet added to chunks** — those come in stage 2.

---

## Ready for Stage 2

The structured JSON files in `03_rfi_qa_json` and `04_commissioning_json` are the inputs for the next stage:

1. Chunking (512–1024 tokens with 15–20% overlap)
2. Per-chunk metadata enrichment (`Document_Type`, `Discipline`, `Equipment_Tag`, `Date`)
3. Embedding with **BGE-M3**
4. Loading into **Qdrant**
5. FastAPI retrieval endpoint

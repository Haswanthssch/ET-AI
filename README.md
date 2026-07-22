# AURA-EPC — Automated Unified Risk & Asset Intelligence
## Hyperscale Data Centre EPC Intelligence Platform

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Groq API key (free at https://console.groq.com)

### 1. Configure API Key

```powershell
# Copy template and add your key
Copy-Item backend\.env.example backend\.env
# Edit backend\.env and set: GROQ_API_KEY=your_key_here
```

### 2. Launch Everything (One Command)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\launch.ps1
```

Or manually:

**Terminal 1 — Backend:**
```powershell
cd N:\ETAI\backend
pip install -r requirements.txt
python bootstrap.py          # generates data + trains model + builds vector index
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd N:\ETAI\frontend
npm install
npm run dev
```

---

## Access URLs

| Service | URL |
|---|---|
| **Executive Dashboard** | http://localhost:3000/executive |
| **Procurement Hub** | http://localhost:3000/procurement |
| **Engineer Copilot** | http://localhost:3000/engineer |
| **QA/QC Command** | http://localhost:3000/qa-qc |
| **FastAPI Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

---

## Architecture

```
AURA-EPC
├── backend/                     # FastAPI + LangGraph + Groq
│   ├── main.py                  # 8 API endpoints
│   ├── agents/
│   │   ├── compliance_agent.py  # Module 1: RAG compliance checker
│   │   ├── risk_engine.py       # Module 2: XGBoost + CPM + Groq mitigations
│   │   ├── rfi_copilot.py       # Module 3: Conversational RAG w/ citations
│   │   ├── commissioning_qa.py  # Module 4: Tier I-IV validator + certificate
│   │   └── vision_parser.py     # Module 5: Groq vision P&ID parser
│   ├── core/
│   │   ├── groq_client.py       # Groq SDK singleton (NOT OpenAI)
│   │   ├── cpm_engine.py        # NetworkX CPM DAG
│   │   ├── ml_model.py          # XGBoost delay predictor
│   │   └── vector_store.py      # FAISS semantic search
│   └── data/
│       ├── generate_epc_data.py # Synthetic data hydration
│       ├── master_schedule.csv  # 500-activity CPM schedule
│       ├── supply_chain.csv     # 50 items (GEN-CAT-01 forced conflict)
│       └── rfi_logs.json        # 50 RFI entries
└── frontend/                    # Next.js 15 + Tailwind + Framer Motion
    └── src/app/
        ├── executive/           # Burgundy theme — risk & SLA
        ├── procurement/         # Amber Gold — supply chain & compliance
        ├── engineer/            # Muted Copper — RFI copilot & vision
        └── qa-qc/               # Emerald Slate — commissioning certs
```

## Key Design Decisions

- **LLM**: Groq `llama-3.3-70b-versatile` exclusively (no OpenAI)
- **Vision**: `qwen3.6-27b` with fallback to `meta-llama/llama-4-scout-17b-16e-instruct`
- **Vector DB**: FAISS (local, no Docker) for MVP
- **Embeddings**: `all-MiniLM-L6-v2` (local, no API cost)
- **Agents**: LangGraph StateGraph with Critic Node self-healing on all 5 modules

## Forced Conflict (Demo Data)

Equipment `GEN-CAT-01` (Caterpillar Generator) is intentionally set to **"Customs Hold"** 
with an 18-day delay, mapped to a critical path task. This powers the live Executive 
dashboard alert and demonstrates the risk cascade analysis.

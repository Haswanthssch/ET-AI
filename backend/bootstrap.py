#!/usr/bin/env python3
"""
AURA-EPC Bootstrap Script
Runs the full initialization pipeline:
  1. Generate synthetic data
  2. Train XGBoost model
  3. Build FAISS vector index
"""
import sys
import os
import runpy

# Change to backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

print("=" * 60)
print("  AURA-EPC Bootstrap Pipeline")
print("=" * 60)

# Step 1: Data Generation
print("\n[STEP 1/3] Generating EPC Data...")
try:
    runpy.run_path("data/generate_epc_data.py", run_name="__main__")
except Exception as e:
    print(f"  [FAIL] Data generation failed: {e}")
    sys.exit(1)

# Step 2: Train XGBoost
print("\n[STEP 2/3] Training XGBoost Delay Predictor...")
try:
    from core.ml_model import train_model
    result = train_model("./data/master_schedule.csv", "./data/supply_chain.csv")
    print(f"  [OK] Model trained: accuracy={result.get('accuracy', 'N/A'):.2%}, samples={result.get('samples', 0)}")
except Exception as e:
    print(f"  [WARN]  ML training failed (non-fatal): {e}")

# Step 3: Build FAISS Vector Index
print("\n[STEP 3/3] Building FAISS Vector Index...")
try:
    import json
    from pathlib import Path
    from core.vector_store import get_vector_store

    documents = []
    rfi_path = Path("./data/rfi_logs.json")
    spec_path = Path("./data/spec_chunks.json")

    if rfi_path.exists():
        with open(rfi_path, encoding="utf-8") as f:
            rfis = json.load(f)
        for rfi in rfis:
            documents.append({
                "id": rfi["rfi_id"],
                "source": "RFI Log",
                "content": f"[{rfi['rfi_id']}] {rfi['title']}\n{rfi['description']}\nResolution: {rfi.get('resolution_notes', 'Pending')}",
                "metadata": {"category": rfi.get("category"), "location": rfi.get("location")},
            })

    if spec_path.exists():
        with open(spec_path, encoding="utf-8") as f:
            specs = json.load(f)
        for spec in specs:
            documents.append({
                "id": spec["id"],
                "source": spec["source"],
                "content": spec["content"],
                "metadata": spec.get("metadata", {}),
            })

    store = get_vector_store()
    store.build_index(documents)
    print(f"  [OK] FAISS index built: {len(documents)} documents indexed")
except Exception as e:
    print(f"  [WARN]  Vector index build failed (non-fatal): {e}")

print("\n" + "=" * 60)
print("  Bootstrap complete! Starting AURA-EPC...")
print("=" * 60)
print()
print("  Backend:  http://localhost:8000")
print("  API Docs: http://localhost:8000/docs")
print("  Frontend: http://localhost:3000")
print()
print("  [WARN]  Don't forget to set GROQ_API_KEY in backend/.env")
print()

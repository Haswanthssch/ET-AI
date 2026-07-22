"""Script to build FAISS vector index from RFI logs and spec chunks."""
import sys
import json
sys.path.insert(0, '.')

from pathlib import Path
from core.vector_store import get_vector_store

documents = []

with open('./data/rfi_logs.json', encoding='utf-8') as f:
    rfis = json.load(f)

for rfi in rfis:
    content = f"[{rfi['rfi_id']}] {rfi['title']}\n{rfi['description']}\nResolution: {rfi.get('resolution_notes', 'Pending')}"
    documents.append({
        'id': rfi['rfi_id'],
        'source': 'RFI Log',
        'content': content,
        'metadata': {'category': rfi.get('category'), 'location': rfi.get('location')},
    })

with open('./data/spec_chunks.json', encoding='utf-8') as f:
    specs = json.load(f)

for spec in specs:
    documents.append({
        'id': spec['id'],
        'source': spec['source'],
        'content': spec['content'],
        'metadata': spec.get('metadata', {}),
    })

print(f'Building FAISS index with {len(documents)} documents...')
store = get_vector_store()
store.build_index(documents)
print(f'FAISS index built successfully! Documents: {len(documents)}')

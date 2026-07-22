import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.auth import router as auth_router
from backend.routers import router as api_router
from backend.core.config import settings

load_dotenv()

app = FastAPI(title="ETAI Backend")

# --- CORS Configuration ---
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth_router)
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the ETAI Backend. Visit /docs for API documentation."}

@app.get("/health")
async def health():
    return {"status": "ok", "groq_key_configured": bool(settings.GROQ_API_KEY)}

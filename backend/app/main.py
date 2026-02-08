"""
CallPilot FastAPI entry point.
Agentic voice AI backend for autonomous appointment scheduling (ElevenLabs CallPilot Challenge).
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from api.routes import appointments, messages, tasks


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load config and ensure data paths exist. No heavy init required for data-driven design."""
    settings = get_settings()
    app.state.settings = settings
    prov_path = getattr(settings, "providers_json_path", None)
    prov_path = Path(prov_path) if prov_path is not None else Path(__file__).resolve().parent.parent / "data" / "providers.json"
    prov_path.parent.mkdir(parents=True, exist_ok=True)
    yield
    # Teardown: nothing to close for MVP


app = FastAPI(
    title="CallPilot API",
    description="Agentic voice AI backend for autonomous dentist appointment scheduling.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["messages"])
app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["appointments"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

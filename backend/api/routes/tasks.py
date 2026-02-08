from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.schemas import TaskCreate, TaskMode, TaskState, TaskStatus
from swarm.controller import run_swarm, run_single_agent

router = APIRouter()

_tasks: Dict[str, TaskState] = {}
_tasks_lock = asyncio.Lock()


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    message: str


async def _run_task(task_id: str, state: TaskState, settings: Any) -> None:
    raw_path = getattr(settings, "providers_json_path", None)
    path = Path(raw_path) if raw_path is not None else Path(__file__).resolve().parent.parent.parent / "data" / "providers.json"
    api_key = getattr(settings, "elevenlabs_api_key", None) or ""
    agent_id = getattr(settings, "elevenlabs_agent_id", None) or ""
    try:
        state.status = TaskStatus.RUNNING
        if state.mode == TaskMode.SWARM:
            outcomes, shortlist, tool_logs = await run_swarm(
                providers_path=path,
                user_request=state.user_request,
                task_id=task_id,
                api_key=api_key,
                agent_id=agent_id,
                max_agents=getattr(settings, "swarm_max_agents", 15),
            )
            state.outcomes = outcomes
            state.shortlist = shortlist
            state.tool_calls_log = tool_logs
        else:
            providers = __import__("core.providers_loader", fromlist=["load_providers"]).load_providers(path)
            provider_id = providers[0].id if providers else ""
            if not provider_id:
                state.status = TaskStatus.FAILED
                state.error_message = "No providers configured"
                return
            outcome, shortlist, tool_logs, transcript = run_single_agent(
                provider_id=provider_id,
                providers_path=path,
                user_request=state.user_request,
                task_id=task_id,
                api_key=api_key,
                agent_id=agent_id,
            )
            state.outcomes = [outcome]
            state.shortlist = shortlist
            state.tool_calls_log = tool_logs
            state.transcript = transcript
        state.status = TaskStatus.COMPLETED
    except Exception as e:
        state.status = TaskStatus.FAILED
        state.error_message = str(e)
    finally:
        from datetime import datetime
        state.updated_at = datetime.utcnow()


@router.post("/", response_model=TaskCreateResponse)
async def create_task(request: Request, body: TaskCreate) -> TaskCreateResponse:
    task_id = str(uuid.uuid4())
    state = TaskState(
        task_id=task_id,
        status=TaskStatus.PENDING,
        mode=body.user_request.mode,
        user_request=body.user_request,
    )
    async with _tasks_lock:
        _tasks[task_id] = state
    settings = getattr(request.app.state, "settings", None)
    if not settings:
        raise HTTPException(status_code=500, detail="App settings not available")

    asyncio.create_task(_run_task(task_id, state, settings))
    return TaskCreateResponse(
        task_id=task_id,
        status=state.status.value,
        message="Task started. Poll GET /tasks/{task_id} for status and results.",
    )


@router.get("/{task_id}")
async def get_task(request: Request, task_id: str) -> TaskState:
    async with _tasks_lock:
        state = _tasks.get(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    return state


@router.get("/")
async def list_tasks() -> dict[str, list[dict]]:
    async with _tasks_lock:
        items = [
            {"task_id": s.task_id, "status": s.status.value, "mode": s.mode.value}
            for s in _tasks.values()
        ]
    return {"tasks": items}

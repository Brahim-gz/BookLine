from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.routes.tasks import _tasks, _tasks_lock

router = APIRouter()


class SendMessageRequest(BaseModel):
    task_id: str
    message: str


class SendMessageResponse(BaseModel):
    ok: bool
    message: str


@router.post("/", response_model=SendMessageResponse)
async def send_message(request: Request, body: SendMessageRequest) -> SendMessageResponse:
    async with _tasks_lock:
        state = _tasks.get(body.task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    return SendMessageResponse(
        ok=True,
        message="Message accepted. Real-time injection into active conversation requires session handle.",
    )

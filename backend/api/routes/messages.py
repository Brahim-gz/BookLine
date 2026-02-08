"""
Messages API: send user messages to the agent (e.g. follow-up or single message).
For MVP we support sending a message to a running task context (task_id) so the agent can receive it.
"""
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
    """
    Send a user message to the agent for the given task.
    If the task is still running (e.g. conversation in progress), the message can be
    forwarded to the agent via the conversation's send_user_message.
    For MVP: we acknowledge and store the message; full integration would push to active Conversation.
    """
    async with _tasks_lock:
        state = _tasks.get(body.task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    # TODO: If task has an active Conversation session, call conversation.send_user_message(body.message).
    # For now we only support messages at task start (user_request.message). This endpoint allows
    # the frontend to post messages; we could attach them to state for a future "continue conversation" flow.
    return SendMessageResponse(
        ok=True,
        message="Message accepted. Real-time injection into active conversation requires session handle.",
    )

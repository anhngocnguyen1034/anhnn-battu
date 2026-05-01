# -*- coding: utf-8 -*-
"""
POST /api/v1/chat/stream — SSE streaming chat endpoint.

Wraps the ReAct agent loop into Server-Sent Events so the Tauri / web
frontend can render tokens in real time.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.schemas.chat import ChatRequest
from backend.services.agent_service import stream_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/stream",
    summary="Streaming AI chat (SSE)",
    description=(
        "Open an SSE connection that streams the ReAct agent's reasoning "
        "and final answer. Events: token, tool_call, status, done, error."
    ),
)
async def post_chat_stream(req: ChatRequest):
    """
    Stream a bazi consultation conversation via Server-Sent Events.

    Each SSE frame has an ``event`` field and a JSON ``data`` payload:

    - ``token``   — ``{"content": "..."}`` real-time text chunk
    - ``status``  — ``{"message": "..."}`` progress indicator
    - ``done``    — ``{"content": "...", "fact_checks": [...]}`` final answer
    - ``error``   — ``{"message": "..."}`` unrecoverable error

    The connection closes after ``done`` or ``error``.
    """

    async def event_generator():
        """Async wrapper around the sync agent generator."""
        loop = asyncio.get_running_loop()

        def _run_stream():
            """Run the sync generator in a thread."""
            yield from stream_chat(
                message=req.message,
                provider=req.provider,
                api_key=req.api_key,
                base_url=req.base_url,
                model=req.model,
                chart_data=req.chart_data,
                history=req.history,
                max_steps=req.max_steps,
            )

        # Run sync generator in thread pool to avoid blocking the event loop.
        queue: asyncio.Queue = asyncio.Queue()
        _SENTINEL = object()

        def _producer():
            try:
                for event_type, payload in _run_stream():
                    loop.call_soon_threadsafe(
                        queue.put_nowait, (event_type, payload)
                    )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, _SENTINEL)

        import threading
        threading.Thread(target=_producer, daemon=True).start()

        while True:
            item = await queue.get()
            if item is _SENTINEL:
                break
            event_type, payload = item
            yield {
                "event": event_type,
                "data": json.dumps(payload, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())

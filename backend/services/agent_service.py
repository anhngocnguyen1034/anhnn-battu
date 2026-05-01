# -*- coding: utf-8 -*-
"""
Agent service — wraps the ReAct streaming loop for SSE delivery.

Translates the generator protocol used by ``run_react_loop_streaming``
(yielding ``str`` tokens, ``[STATUS]`` prefixes, and a final ``tuple``)
into a uniform ``(event_type, data)`` stream consumed by the chat router.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

from agent.api_adapter import create_client
from agent.react_agent import run_react_loop_streaming
from prompts.system_prompts import build_system_prompt
from tools.bazi_tools import TOOL_SCHEMAS, dispatch_tool
from backend.config import settings

logger = logging.getLogger(__name__)


def stream_chat(
    *,
    message: str,
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    chart_data: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    max_steps: int = 8,
) -> Generator[Tuple[str, Any], None, None]:
    """
    Run the ReAct agent and yield ``(event_type, payload)`` tuples.

    The caller (SSE router) is responsible for formatting these into
    ``EventSourceResponse`` frames.

    Event types emitted:
      - ``"status"``  — progress messages (tool calls, etc.)
      - ``"token"``   — real-time text chunks from the LLM
      - ``"done"``    — final answer + optional fact-check results
      - ``"error"``   — unrecoverable error

    Args:
        message: User's latest message.
        provider: AI provider name (``"OpenAI"`` or ``"MiMo"``).
        api_key: Provider API key.
        base_url: Provider base URL.
        model: Model identifier.
        chart_data: Pre-computed bazi chart (from /chart).
        history: Previous conversation turns ``[{role, content}, ...]``.
        max_steps: ReAct loop depth limit.

    Yields:
        ``(event_type: str, data: Any)``
    """
    chart_data = chart_data or {}

    # 从配置文件自动填充缺失的 API 参数
    if not api_key or not base_url or not model:
        if provider in ("GLM", "Zhipu"):
            api_key = api_key or settings.ANTHROPIC_API_KEY
            base_url = base_url or settings.ANTHROPIC_BASE_URL
            model = model or "glm-5.1"
        else:
            api_key = api_key or settings.OPENAI_API_KEY
            base_url = base_url or settings.OPENAI_BASE_URL
            model = model or settings.OPENAI_MODEL

    # Build system prompt from chart data
    try:
        system_prompt = build_system_prompt(chart_data)
    except Exception:
        logger.warning("Failed to build system prompt", exc_info=True)
        system_prompt = "你是一位专业的命理大师。"

    # Assemble messages
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if history:
        for turn in history:
            if isinstance(turn, dict) and "role" in turn and "content" in turn:
                messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    # Create client
    try:
        client_info = create_client(provider, api_key, base_url)
    except Exception as exc:
        logger.error("Failed to create API client: %s", exc)
        yield ("error", {"message": "无法创建 API 客户端，请检查 API Key 和 Base URL 配置。"})
        return

    # Run the streaming ReAct loop
    try:
        gen = run_react_loop_streaming(
            client_info=client_info,
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            dispatch_tool=dispatch_tool,
            bazi_data=chart_data,
            max_steps=max_steps,
            do_fact_check=True,
        )

        for item in gen:
            if isinstance(item, tuple):
                # Final result: (final_content, updated_messages, fact_check_results)
                final_content, _updated_msgs, fact_checks = item
                yield ("done", {
                    "content": final_content,
                    "fact_checks": fact_checks,
                })
            elif isinstance(item, str) and item.startswith("[STATUS] "):
                yield ("status", {"message": item[9:]})
            elif isinstance(item, str):
                yield ("token", {"content": item})
            else:
                # Unexpected type — skip
                logger.debug("Unexpected yield type from agent: %s", type(item))

    except Exception as exc:
        logger.error("Agent streaming failed: %s", exc, exc_info=True)
        yield ("error", {"message": "AI 分析过程中出现错误，请稍后重试。"})

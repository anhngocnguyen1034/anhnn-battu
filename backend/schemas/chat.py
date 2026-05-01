# -*- coding: utf-8 -*-
"""
Request / response models for the /chat/stream SSE endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /api/v1/chat/stream — initiate a streaming AI conversation."""

    message: str = Field(
        ...,
        max_length=10000,
        description="用户消息文本",
        examples=["请分析一下我的八字格局和事业运势"],
    )
    provider: str = Field(
        default="OpenAI",
        description="AI 服务商名称：OpenAI (MiniMax) | GLM (智谱)",
        examples=["OpenAI", "GLM"],
    )
    api_key: str = Field(
        default="",
        description="API 密钥（可从配置文件自动填充）",
    )
    base_url: str = Field(
        default="",
        description="API 基础 URL（可从配置文件自动填充）",
    )
    model: str = Field(
        default="",
        description="模型名称（可从配置文件自动填充）",
    )
    chart_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="已计算的八字命盘数据（来自 /chart 端点）",
    )
    history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        max_length=50,
        description="对话历史 [{role, content}, ...]",
    )
    max_steps: int = Field(
        default=8,
        ge=1,
        le=16,
        description="ReAct 循环最大步数",
    )


class ChatSSEEvent(BaseModel):
    """A single Server-Sent Event in the chat stream."""

    event: str = Field(
        ...,
        description="事件类型：token | tool_call | status | done | error",
    )
    data: Any = Field(
        ...,
        description="事件载荷，格式随 event 类型而异",
    )

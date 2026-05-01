# -*- coding: utf-8 -*-
"""
API 适配层 — 统一 OpenAI 与 Anthropic SDK 的调用接口。

设计目标：
  - 上层代码（ReAct 循环、Streamlit UI）无需关心底层 SDK 差异
  - MiMo 等使用 Anthropic Messages API 的服务通过此层透明接入
  - 新增服务商只需在 ANTHROPIC_PROVIDERS 集合中注册

使用方式：
    client_info = create_client("MiMo", api_key, base_url)
    result = call_api(client_info, model, messages, tools=tools)
    # result = {"content": str, "tool_calls": list, "raw": Any}

    # 流式调用
    for item in call_api_streaming(client_info, model, messages):
        if isinstance(item, tuple):
            content, tool_calls = item
        else:
            print(item, end="")  # 实时内容片段
"""

import json
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

# ── 配置 ─────────────────────────────────────────────────────────────────────

# 使用 Anthropic Messages API 的服务商集合。
# 新增 Anthropic 兼容服务商时，只需在此添加名称。
ANTHROPIC_PROVIDERS: set = {"MiMo", "GLM", "Zhipu", "智谱 GLM", "Anthropic (兼容)"}

# Anthropic 响应中的 content block 类型
_BLOCK_TYPE_TEXT = "text"
_BLOCK_TYPE_TOOL_USE = "tool_use"
_BLOCK_TYPE_THINKING = "thinking"


# ── 公共接口 ─────────────────────────────────────────────────────────────────

def is_anthropic_provider(provider_name: str) -> bool:
    """判断指定服务商是否使用 Anthropic API 格式。"""
    return provider_name in ANTHROPIC_PROVIDERS


def create_client(provider_name: str, api_key: str, base_url: str) -> dict:
    """
    根据服务商类型创建对应的 API 客户端。

    Args:
        provider_name: 服务商名称（如 "MiMo", "OpenAI", "阿里云百炼"）
        api_key: API 密钥
        base_url: API 基础 URL

    Returns:
        dict: {"type": "anthropic"|"openai", "client": SDK客户端实例}
    """
    if is_anthropic_provider(provider_name):
        from anthropic import Anthropic
        return {"type": "anthropic", "client": Anthropic(api_key=api_key, base_url=base_url)}
    else:
        from openai import OpenAI
        return {"type": "openai", "client": OpenAI(api_key=api_key, base_url=base_url)}


def call_api(
    client_info: dict,
    model: str,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.6,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """
    统一的非流式 API 调用。

    Args:
        client_info: create_client() 返回的客户端信息
        model: 模型名称
        messages: 消息列表（OpenAI 格式）
        tools: 工具 schema 列表（可选）
        temperature: 温度参数
        max_tokens: 最大生成 token 数

    Returns:
        dict: {
            "content": str,       # 模型生成的文本内容
            "tool_calls": list,   # 工具调用列表（可能为空）
            "raw": Any,           # 原始 SDK 响应对象
        }
    """
    if client_info["type"] == "anthropic":
        return _call_anthropic(client_info["client"], model, messages, tools, temperature, max_tokens)
    return _call_openai(client_info["client"], model, messages, tools, temperature, max_tokens)


def call_api_streaming(
    client_info: dict,
    model: str,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.6,
    max_tokens: int = 4096,
) -> Generator[Union[str, Tuple[str, list]], None, None]:
    """
    统一的流式 API 调用（生成器）。

    Yield 协议：
      - str: 实时内容片段，可直接拼接显示
      - tuple: (final_content, tool_calls) 作为最终结果，总是最后 yield

    Args:
        client_info: create_client() 返回的客户端信息
        model: 模型名称
        messages: 消息列表
        tools: 工具 schema 列表（可选）
        temperature: 温度参数
        max_tokens: 最大生成 token 数

    Yields:
        str 或 (str, list) 元组
    """
    if client_info["type"] == "anthropic":
        yield from _stream_anthropic(client_info["client"], model, messages, tools, temperature, max_tokens)
    else:
        yield from _stream_openai(client_info["client"], model, messages, tools, temperature, max_tokens)


# ── 内部实现：OpenAI ────────────────────────────────────────────────────────

def _call_openai(client, model, messages, tools, temperature, max_tokens):
    """OpenAI 非流式调用。"""
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    resp = client.chat.completions.create(**kwargs)
    msg = resp.choices[0].message

    tool_calls = []
    if msg.tool_calls:
        for tc in msg.tool_calls:
            tool_calls.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            })

    return {"content": (msg.content or "").strip(), "tool_calls": tool_calls, "raw": resp}


def _stream_openai(client, model, messages, tools, temperature, max_tokens):
    """OpenAI 流式调用。"""
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    stream = client.chat.completions.create(**kwargs)
    content = ""
    tool_calls_acc: Dict[int, Dict[str, Any]] = {}

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        # 累积工具调用片段（OpenAI 的 tool_calls 通过多个 chunk 拼接）
        if delta.tool_calls:
            for tc_delta in delta.tool_calls:
                idx = tc_delta.index
                if idx not in tool_calls_acc:
                    tool_calls_acc[idx] = {"id": "", "name": "", "arguments": ""}
                if tc_delta.id:
                    tool_calls_acc[idx]["id"] = tc_delta.id
                if tc_delta.function:
                    if tc_delta.function.name:
                        tool_calls_acc[idx]["name"] = tc_delta.function.name
                    if tc_delta.function.arguments:
                        tool_calls_acc[idx]["arguments"] += tc_delta.function.arguments
        elif delta.content:
            content += delta.content
            yield delta.content

    # 整理工具调用列表
    tool_calls = []
    for idx in sorted(tool_calls_acc.keys()):
        tc = tool_calls_acc[idx]
        tool_calls.append({
            "id": tc["id"],
            "type": "function",
            "function": {"name": tc["name"], "arguments": tc["arguments"]},
        })

    yield (content, tool_calls)


# ── 内部实现：Anthropic ─────────────────────────────────────────────────────

def _extract_anthropic_content(response) -> str:
    """
    从 Anthropic Messages API 响应中提取文本内容。

    MiMo 等模型可能返回 ThinkingBlock（推理过程），此处只提取最终文本。
    """
    texts = []
    for block in response.content:
        block_type = getattr(block, "type", None)
        if block_type == _BLOCK_TYPE_THINKING:
            # 跳过推理过程，只取最终回答
            continue
        if hasattr(block, "text"):
            texts.append(block.text)
    return "\n".join(texts)


def _convert_messages_to_anthropic(messages: List[Dict[str, Any]]) -> Tuple[str, List[Dict]]:
    """
    将 OpenAI 格式的消息列表转换为 Anthropic Messages API 格式。

    转换规则：
      - 提取 system 消息为独立的 system 参数
      - tool 角色消息转为 user 消息中的 tool_result content block
      - assistant 的 tool_calls 转为 tool_use content block

    Returns:
        (system_text, converted_messages)
    """
    system_text = ""
    converted = []

    for m in messages:
        role = m.get("role", "user")

        # system 消息单独提取，Anthropic API 用 system 参数传递
        if role == "system":
            system_text = m.get("content", "")
            continue

        # tool 结果消息：转为 user 角色的 tool_result block
        if role == "tool":
            converted.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id", ""),
                    "content": m.get("content", ""),
                }],
            })
            continue

        # assistant 消息中包含 tool_calls：转为 tool_use block
        if role == "assistant" and m.get("tool_calls"):
            content_blocks = []
            if m.get("content"):
                content_blocks.append({"type": "text", "text": m["content"]})
            for tc in m["tool_calls"]:
                fn = tc.get("function", {})
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                content_blocks.append({
                    "type": "tool_use",
                    "id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "input": args,
                })
            converted.append({"role": "assistant", "content": content_blocks})
            continue

        # 普通 user/assistant 消息
        converted.append({"role": role, "content": m.get("content", "")})

    # Anthropic API requires at least one message in the messages array.
    # If only a system message was provided, add a minimal user message.
    if not converted:
        converted.append({"role": "user", "content": "..."})

    return system_text, converted


def _convert_tools_to_anthropic(tools: List[Dict[str, Any]]) -> List[Dict]:
    """将 OpenAI function calling schema 转换为 Anthropic tool schema。"""
    anthropic_tools = []
    for t in tools:
        fn = t.get("function", {})
        anthropic_tools.append({
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {}),
        })
    return anthropic_tools


def _call_anthropic(client, model, messages, tools, temperature, max_tokens):
    """Anthropic 非流式调用。"""
    system_text, converted = _convert_messages_to_anthropic(messages)

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": converted,
    }
    if system_text:
        kwargs["system"] = system_text
    if tools:
        kwargs["tools"] = _convert_tools_to_anthropic(tools)

    resp = client.messages.create(**kwargs)

    # 提取文本内容和工具调用
    content = ""
    tool_calls = []
    for block in resp.content:
        block_type = getattr(block, "type", None)
        if block_type == _BLOCK_TYPE_THINKING:
            continue  # 跳过推理过程
        if hasattr(block, "text"):
            content += block.text
        elif block_type == _BLOCK_TYPE_TOOL_USE:
            tool_calls.append({
                "id": block.id,
                "type": "function",
                "function": {
                    "name": block.name,
                    "arguments": json.dumps(block.input, ensure_ascii=False),
                },
            })

    return {"content": content.strip(), "tool_calls": tool_calls, "raw": resp}


def _stream_anthropic(client, model, messages, tools, temperature, max_tokens):
    """Anthropic 流式调用。"""
    system_text, converted = _convert_messages_to_anthropic(messages)

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": converted,
    }
    if system_text:
        kwargs["system"] = system_text
    if tools:
        kwargs["tools"] = _convert_tools_to_anthropic(tools)

    content = ""
    tool_calls = []

    with client.messages.stream(**kwargs) as stream:
        for event in stream:
            event_type = getattr(event, "type", None)

            # 工具调用开始：记录新的 tool_use block
            if event_type == "content_block_start":
                block = event.content_block
                if getattr(block, "type", None) == _BLOCK_TYPE_TOOL_USE:
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {"name": block.name, "arguments": ""},
                    })

            # 内容增量：文本片段或工具参数片段
            elif event_type == "content_block_delta":
                delta = event.delta
                if hasattr(delta, "text"):
                    content += delta.text
                    yield delta.text
                elif hasattr(delta, "partial_json") and tool_calls:
                    # 工具调用的 JSON 参数通过多个 chunk 拼接
                    tool_calls[-1]["function"]["arguments"] += delta.partial_json

    yield (content, tool_calls)

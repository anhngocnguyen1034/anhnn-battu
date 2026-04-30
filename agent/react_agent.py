# -*- coding: utf-8 -*-
"""
ReAct Agent 循环：Thought -> Action -> Observation -> ... -> Final Answer。
支持一次对话中多次调用不同工具，可选 Fact-Check 校验流年干支。
"""
import json
from typing import Any, Callable, Dict, List, Tuple

from tools.bazi_tools import extract_ganzhi_from_text, fact_check_ganzhi


def run_react_loop(
    client: Any,
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    dispatch_tool: Callable[[str, Dict[str, Any], Dict[str, Any] | None], str],
    bazi_data: Dict[str, Any] | None = None,
    *,
    max_steps: int = 8,
    tool_choice: str = "auto",
    do_fact_check: bool = True,
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    执行 ReAct 循环直至模型返回无 tool_calls 的最终回答，或达到 max_steps。
    返回 (final_content, updated_messages, fact_check_results)。
    fact_check_results 为列表，每项为 {"year", "claimed", "actual", "match"}。
    """
    bazi_data = bazi_data or {}
    working = list(messages)
    step = 0
    final_content = ""

    while step < max_steps:
        step += 1
        resp = client.chat.completions.create(
            model=model,
            messages=working,
            tools=tools,
            tool_choice=tool_choice,
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            final_content = (msg.content or "").strip() or "天机不可泄露。"
            working.append({"role": "assistant", "content": final_content})
            break

        assistant_msg = {
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": t.id,
                    "type": getattr(t, "type", "function"),
                    "function": {
                        "name": t.function.name,
                        "arguments": t.function.arguments,
                    },
                }
                for t in msg.tool_calls
            ],
        }
        working.append(assistant_msg)

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = dispatch_tool(name, args, bazi_data)
            working.append({
                "tool_call_id": tc.id,
                "role": "tool",
                "name": name,
                "content": result,
            })

    fact_check_results: List[Dict[str, Any]] = []
    if do_fact_check and final_content:
        for year, claimed in extract_ganzhi_from_text(final_content):
            data = json.loads(fact_check_ganzhi(claimed, year))
            if not data.get("match"):
                fact_check_results.append({
                    "year": year,
                    "claimed": data.get("claimed"),
                    "actual": data.get("actual"),
                    "match": False,
                })

    return final_content, working, fact_check_results


# ---------------------------------------------------------------------------
# Streaming variant
# ---------------------------------------------------------------------------

def run_react_loop_streaming(
    client: Any,
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    dispatch_tool: Callable[[str, Dict[str, Any], Dict[str, Any] | None], str],
    bazi_data: Dict[str, Any] | None = None,
    *,
    max_steps: int = 8,
    tool_choice: str = "auto",
    do_fact_check: bool = True,
):
    """
    Streaming 版本的 ReAct 循环。

    生成器 yield 协议：
      - str  : 以 "[STATUS] " 开头表示状态消息（工具调用中等），否则为文本内容片段
      - tuple: (final_content, updated_messages, fact_check_results) 作为最终结果

    调用方示例 ::
        gen = run_react_loop_streaming(...)
        for item in gen:
            if isinstance(item, tuple):
                final_content, messages, fc = item
            elif item.startswith("[STATUS] "):
                show_status(item.removeprefix("[STATUS] "))
            else:
                stream_to_ui(item)
    """
    bazi_data = bazi_data or {}
    working = list(messages)
    step = 0
    final_content = ""

    while step < max_steps:
        step += 1

        # Use streaming for every API call so we can detect tool calls early
        stream = client.chat.completions.create(
            model=model,
            messages=working,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
        )

        # Accumulators for this streaming response
        tool_calls_acc: Dict[int, Dict[str, Any]] = {}   # index -> partial tool call
        content_prefix = ""

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            # --- Tool call deltas (accumulate JSON fragments) ---
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {
                            "id": tc_delta.id or "",
                            "type": getattr(tc_delta, "type", None) or "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    entry = tool_calls_acc[idx]
                    if tc_delta.id:
                        entry["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            entry["function"]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            entry["function"]["arguments"] += tc_delta.function.arguments

            # --- Content deltas (yield immediately for streaming display) ---
            elif delta.content:
                content_prefix += delta.content
                yield delta.content

        # --- After stream exhausted: decide tool-call vs final answer ---
        if not tool_calls_acc:
            # No tool calls => this is the final answer
            final_content = content_prefix.strip() or "天机不可泄露。"
            working.append({"role": "assistant", "content": final_content})
            break

        # Tool calls present => execute them
        ordered_tcs = [tool_calls_acc[i] for i in sorted(tool_calls_acc)]
        assistant_msg = {
            "role": "assistant",
            "content": content_prefix or "",
            "tool_calls": ordered_tcs,
        }
        working.append(assistant_msg)

        for tc in ordered_tcs:
            name = tc["function"]["name"]
            tool_id = tc["id"]
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            yield f"[STATUS] 正在调用工具 {name}..."
            result = dispatch_tool(name, args, bazi_data)
            working.append({
                "tool_call_id": tool_id,
                "role": "tool",
                "name": name,
                "content": result,
            })

    # --- Fact check ---
    fact_check_results: List[Dict[str, Any]] = []
    if do_fact_check and final_content:
        for year, claimed in extract_ganzhi_from_text(final_content):
            data = json.loads(fact_check_ganzhi(claimed, year))
            if not data.get("match"):
                fact_check_results.append({
                    "year": year,
                    "claimed": data.get("claimed"),
                    "actual": data.get("actual"),
                    "match": False,
                })

    yield (final_content, working, fact_check_results)

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

# -*- coding: utf-8 -*-
"""
多轮对话上下文管理：维护 messages，超 token 阈值时压缩旧对话，保留 system + 最近 N 轮 + 摘要。
"""
from typing import Any, Dict, List

DEFAULT_TOKEN_THRESHOLD = 4000
DEFAULT_RECENT_TURNS = 6


def count_tokens_approx(messages: List[Dict[str, Any]]) -> int:
    """
    粗略估计消息列表的 token 数（按字符数 / 2 近似，中文约 1.5 字/token）。
    """
    total = 0
    for m in messages:
        content = m.get("content") or ""
        if isinstance(content, str):
            total += len(content) // 2 + len(content) // 3
        for tc in m.get("tool_calls") or []:
            args = (tc.get("function") or {}).get("arguments") or ""
            total += len(args) // 2
    return total


def build_compressed_messages(
    messages: List[Dict[str, Any]],
    *,
    token_threshold: int = DEFAULT_TOKEN_THRESHOLD,
    recent_turns: int = DEFAULT_RECENT_TURNS,
    summary_placeholder: str = "[此前对话已压缩为摘要，供上下文延续。]",
) -> List[Dict[str, Any]]:
    """
    当 messages 超过 token_threshold 时，保留第一条 system，将中间对话压缩为一条摘要，
    保留最近 recent_turns 轮完整对话。若未超阈值则原样返回。
    """
    if not messages:
        return messages
    approx = count_tokens_approx(messages)
    if approx <= token_threshold:
        return messages

    system_msg = messages[0] if messages and messages[0].get("role") == "system" else None
    rest = messages[1:] if system_msg else messages
    if recent_turns <= 0 or len(rest) <= recent_turns:
        mid = [{"role": "system", "content": summary_placeholder}] if summary_placeholder else []
        return (([system_msg] if system_msg else []) + mid + rest)

    keep_count = recent_turns * 2
    to_compress = rest[:-keep_count] if len(rest) > keep_count else []
    kept = rest[-keep_count:] if len(rest) > keep_count else rest

    summary = summary_placeholder
    if to_compress:
        summary = summary + f"（原约 {len(to_compress)} 条消息已省略）"

    out = []
    if system_msg:
        out.append(system_msg)
    out.append({"role": "system", "content": summary})
    out.extend(kept)
    return out


def get_messages_for_api(
    session_messages: List[Dict[str, Any]],
    token_threshold: int = DEFAULT_TOKEN_THRESHOLD,
    recent_turns: int = DEFAULT_RECENT_TURNS,
) -> List[Dict[str, Any]]:
    """
    从 session_state 的 messages 中取出适合发给 API 的列表（自动压缩）。
    """
    return build_compressed_messages(
        session_messages,
        token_threshold=token_threshold,
        recent_turns=recent_turns,
    )

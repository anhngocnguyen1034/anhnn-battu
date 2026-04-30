# -*- coding: utf-8 -*-
"""
多轮对话上下文管理：维护 messages，超 token 阈值时压缩旧对话，保留 system + 最近 N 轮 + 摘要。
支持可选的 LLM 摘要，将旧对话压缩为有意义的总结而非简单占位符。
"""
import re
from typing import Any, Dict, List, Optional

DEFAULT_TOKEN_THRESHOLD = 4000
DEFAULT_RECENT_TURNS = 6

_SUMMARY_PROMPT = "请用2-3句话总结以下命理对话的要点，保留关键结论和用户关心的问题："
_FALLBACK_SUMMARY = "[此前对话已压缩为摘要，供上下文延续。]"


def _count_cjk(text: str) -> int:
    """统计字符串中的 CJK 字符数。"""
    return len(re.findall(r'[一-鿿㐀-䶿\U00020000-\U0002a6df]', text))


def _count_latin_words(text: str) -> int:
    """统计字符串中的拉丁单词数。"""
    return len(re.findall(r'[a-zA-Z]+', text))


def count_tokens_approx(messages: List[Dict[str, Any]]) -> int:
    """
    粗略估计消息列表的 token 数。
    中文字符约 1.5 chars/token，英文单词约 0.75 words/token。
    简单启发式：分别统计中英文字符，用不同权重加总。
    """
    total = 0
    for m in messages:
        content = m.get("content") or ""
        if isinstance(content, str):
            cjk = _count_cjk(content)
            latin = _count_latin_words(content)
            other = len(content) - cjk - sum(len(w) for w in re.findall(r'[a-zA-Z]+', content))
            # CJK: ~1.5 chars per token => ~0.67 tokens per char
            # Latin words: ~0.75 words per token => ~1.33 tokens per word
            # Other (punctuation, digits, spaces): ~4 chars per token
            total += int(cjk * 0.67 + latin * 1.33 + other * 0.25)
        for tc in m.get("tool_calls") or []:
            args = (tc.get("function") or {}).get("arguments") or ""
            cjk = _count_cjk(args)
            latin = _count_latin_words(args)
            other = len(args) - cjk - sum(len(w) for w in re.findall(r'[a-zA-Z]+', args))
            total += int(cjk * 0.67 + latin * 1.33 + other * 0.25)
    return total


def summarize_messages(
    messages_to_compress: List[Dict[str, Any]],
    client: Any = None,
) -> str:
    """
    使用 LLM 对待压缩的消息进行摘要。
    若 client 为 None，则回退到占位符文本。

    Args:
        messages_to_compress: 需要被压缩的旧消息列表。
        client: OpenAI 兼容客户端，为 None 时使用占位符。

    Returns:
        摘要文本字符串。
    """
    if not messages_to_compress:
        return _FALLBACK_SUMMARY

    if client is None:
        return _FALLBACK_SUMMARY

    # 将待压缩消息拼成一段文本
    parts: List[str] = []
    for m in messages_to_compress:
        role = m.get("role", "")
        content = m.get("content") or ""
        if role == "system":
            continue  # 跳过 system 消息，它会单独保留
        if content:
            label = {"user": "用户", "assistant": "大师"}.get(role, role)
            parts.append(f"{label}: {content[:500]}")
    if not parts:
        return _FALLBACK_SUMMARY

    conversation_text = "\n".join(parts)
    prompt = f"{_SUMMARY_PROMPT}\n\n{conversation_text}"

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        summary = (resp.choices[0].message.content or "").strip()
        if summary:
            return f"[对话摘要] {summary}"
    except Exception:
        pass  # 摘要失败时回退

    return _FALLBACK_SUMMARY


def build_compressed_messages(
    messages: List[Dict[str, Any]],
    *,
    token_threshold: int = DEFAULT_TOKEN_THRESHOLD,
    recent_turns: int = DEFAULT_RECENT_TURNS,
    client: Any = None,
) -> List[Dict[str, Any]]:
    """
    当 messages 超过 token_threshold 时，保留第一条 system，将中间对话压缩为一条摘要，
    保留最近 recent_turns 轮完整对话。若未超阈值则原样返回。

    Args:
        client: OpenAI 兼容客户端。传入时使用 LLM 摘要旧对话；为 None 时使用占位符。
    """
    if not messages:
        return messages
    approx = count_tokens_approx(messages)
    if approx <= token_threshold:
        return messages

    system_msg = messages[0] if messages and messages[0].get("role") == "system" else None
    rest = messages[1:] if system_msg else messages
    if recent_turns <= 0 or len(rest) <= recent_turns:
        mid = [{"role": "system", "content": _FALLBACK_SUMMARY}]
        return (([system_msg] if system_msg else []) + mid + rest)

    keep_count = recent_turns * 2
    to_compress = rest[:-keep_count] if len(rest) > keep_count else []
    kept = rest[-keep_count:] if len(rest) > keep_count else rest

    summary_text = summarize_messages(to_compress, client=client)

    out = []
    if system_msg:
        out.append(system_msg)
    out.append({"role": "system", "content": summary_text})
    out.extend(kept)
    return out


def get_messages_for_api(
    session_messages: List[Dict[str, Any]],
    token_threshold: int = DEFAULT_TOKEN_THRESHOLD,
    recent_turns: int = DEFAULT_RECENT_TURNS,
    client: Any = None,
) -> List[Dict[str, Any]]:
    """
    从 session_state 的 messages 中取出适合发给 API 的列表（自动压缩）。

    Args:
        client: OpenAI 兼容客户端，传入时启用 LLM 摘要。
    """
    return build_compressed_messages(
        session_messages,
        token_threshold=token_threshold,
        recent_turns=recent_turns,
        client=client,
    )

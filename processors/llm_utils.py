"""
LLM 调用辅助工具
"""

import json
from typing import Iterable, List


def parse_json_response(text: str):
    """尽量从模型响应中提取 JSON。"""
    if not text:
        return {}

    cleaned = text.strip()

    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    decoder = json.JSONDecoder()

    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        if start == -1:
            continue

        candidate = cleaned[start:]
        try:
            parsed, _ = decoder.raw_decode(candidate)
            return parsed
        except json.JSONDecodeError:
            end = cleaned.rfind(closer)
            if end != -1 and end >= start:
                snippet = cleaned[start:end + 1]
                try:
                    parsed, _ = decoder.raw_decode(snippet)
                    return parsed
                except json.JSONDecodeError:
                    continue

    return json.loads(cleaned)


def chunk_text(text: str, max_chars: int = 6000, overlap: int = 400) -> List[str]:
    """按字符数切分长文本，避免一次请求过长。"""
    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(text_length, start + max_chars)
        chunks.append(text[start:end])
        if end >= text_length:
            break
        start = max(0, end - overlap)

    return chunks


def merge_unique_dicts(items: Iterable[dict], key_fields: List[str]) -> List[dict]:
    """按多个字段去重并保留原始顺序。"""
    merged = []
    seen = set()

    for item in items:
        key = tuple(str(item.get(field, "")).strip().lower() for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)

    return merged

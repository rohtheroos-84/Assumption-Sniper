from __future__ import annotations

from typing import Iterable, TypeVar

T = TypeVar("T")


def chunk_items(items: Iterable[T], batch_size: int) -> list[list[T]]:
    if batch_size < 1:
        batch_size = 1
    batches: list[list[T]] = []
    current: list[T] = []
    for item in items:
        current.append(item)
        if len(current) >= batch_size:
            batches.append(current)
            current = []
    if current:
        batches.append(current)
    return batches


def join_assumption_texts(texts: list[str], *, max_chars: int = 12000) -> str:
    parts: list[str] = []
    total = 0
    for text in texts:
        snippet = text.strip()
        if not snippet:
            continue
        if total + len(snippet) + 2 > max_chars:
            break
        parts.append(snippet)
        total += len(snippet) + 2
    return "\n".join(parts)

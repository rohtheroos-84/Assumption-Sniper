from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


@dataclass(frozen=True)
class PageResult(Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool
    limit: int


def clamp_limit(limit: int | None, *, default: int, maximum: int) -> int:
    if limit is None:
        return default
    return max(1, min(limit, maximum))


async def paginate_by_id(
    session: AsyncSession,
    stmt: Select[tuple[T]],
    *,
    id_column: Any,
    limit: int,
    cursor: str | None = None,
) -> PageResult[T]:
    query = stmt
    if cursor:
        query = query.where(id_column > cursor)
    query = query.order_by(id_column.asc()).limit(limit + 1)
    rows = (await session.execute(query)).scalars().all()
    has_more = len(rows) > limit
    items = list(rows[:limit])
    next_cursor = items[-1].id if has_more and items else None
    return PageResult(items=items, next_cursor=next_cursor, has_more=has_more, limit=limit)


def serialize_page(items: Sequence[Any], page: PageResult[Any], serializer) -> dict[str, Any]:
    return {
        "items": [serializer(item) for item in items],
        "next_cursor": page.next_cursor,
        "has_more": page.has_more,
        "limit": page.limit,
    }

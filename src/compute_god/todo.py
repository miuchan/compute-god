"""Modern todo list primitives built with a 2020s Python toolchain.

The repository celebrates playful interpretations of scientific metaphors.  To
match that spirit this module implements a small but expressive todo list using
contemporary Python features:

* :class:`enum.StrEnum` for ergonomic string based enumerations.
* :class:`dataclasses.dataclass` with ``slots`` and ``kw_only`` semantics for
  predictable, memory friendly records.
* Immutable value objects that expose purely functional update helpers; this
  makes undo/redo features trivial to build on top while keeping tests
  deterministic.

The public API revolves around two building blocks: :class:`TodoItem`, an
immutable record describing a single task, and :class:`TodoList`, a container
that manages transitions, filtering and serialisation.  While intentionally
minimalistic, the API mirrors the ergonomics of popular "latest tech stack"
frameworks—type annotations everywhere, UTC-aware timestamps and payload
builders ready for JSON responses.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4


class TodoStatus(StrEnum):
    """Lifecycle for a task inside the todo list."""

    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"

    @property
    def is_completed(self) -> bool:
        return self is TodoStatus.COMPLETED


class TodoPriority(StrEnum):
    """Relative urgency for a todo entry."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def weight(self) -> int:
        """Numerical weight used when ordering tasks."""

        return {self.LOW: 0, self.MEDIUM: 1, self.HIGH: 2}[self]


def _ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC)


def _normalise_tags(tags: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalised: list[str] = []
    for tag in tags:
        stripped = tag.strip().lower()
        if not stripped:
            raise ValueError("tags must contain at least one non-whitespace character")
        if stripped not in seen:
            seen.add(stripped)
            normalised.append(stripped)
    return tuple(normalised)


@dataclass(frozen=True, slots=True, kw_only=True)
class TodoItem:
    """Immutable description of a single todo entry."""

    title: str
    description: str = ""
    status: TodoStatus = TodoStatus.PENDING
    due_at: datetime | None = None
    tags: tuple[str, ...] = ()
    priority: TodoPriority = TodoPriority.MEDIUM
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    identifier: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(self, "due_at", _ensure_utc(self.due_at))
        object.__setattr__(self, "created_at", _ensure_utc(self.created_at))
        object.__setattr__(self, "updated_at", _ensure_utc(self.updated_at))
        object.__setattr__(self, "started_at", _ensure_utc(self.started_at))
        object.__setattr__(self, "completed_at", _ensure_utc(self.completed_at))
        object.__setattr__(self, "tags", _normalise_tags(self.tags))
        if not self.title.strip():
            raise ValueError("title must contain at least one non-whitespace character")

    def touch(self, *, timestamp: datetime | None = None) -> Self:
        ts = _ensure_utc(timestamp) or datetime.now(UTC)
        return replace(self, updated_at=ts)

    def with_status(self, status: TodoStatus, *, timestamp: datetime | None = None) -> Self:
        ts = _ensure_utc(timestamp) or datetime.now(UTC)
        started_at = self.started_at
        completed_at = self.completed_at
        if status is TodoStatus.IN_PROGRESS and started_at is None:
            started_at = ts
            completed_at = None
        elif status is TodoStatus.COMPLETED:
            completed_at = ts
            if started_at is None:
                started_at = ts
        elif status is TodoStatus.PENDING:
            started_at = None
            completed_at = None
        return replace(
            self,
            status=status,
            updated_at=ts,
            started_at=started_at,
            completed_at=completed_at,
        )

    def with_tags(self, tags: Iterable[str]) -> Self:
        return replace(self, tags=_normalise_tags(tags), updated_at=datetime.now(UTC))

    def with_due_date(self, due_at: datetime | None) -> Self:
        return replace(self, due_at=_ensure_utc(due_at), updated_at=datetime.now(UTC))

    def with_priority(self, priority: TodoPriority) -> Self:
        return replace(self, priority=priority, updated_at=datetime.now(UTC))

    def to_payload(self) -> Mapping[str, object]:
        return {
            "id": str(self.identifier),
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "tags": list(self.tags),
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass(frozen=True, slots=True)
class TodoStatistics:
    total: int
    pending: int
    in_progress: int
    completed: int

    @property
    def completion_ratio(self) -> float:
        if self.total == 0:
            return 0.0
        return self.completed / self.total


@dataclass(slots=True)
class TodoList:
    """Collection of todo items with convenience helpers."""

    _items: MutableMapping[UUID, TodoItem] = field(default_factory=dict)

    def add(
        self,
        title: str,
        description: str = "",
        *,
        due_at: datetime | None = None,
        tags: Iterable[str] = (),
        priority: TodoPriority = TodoPriority.MEDIUM,
    ) -> TodoItem:
        item = TodoItem(
            title=title,
            description=description,
            due_at=due_at,
            tags=tuple(tags),
            priority=priority,
        )
        self._items[item.identifier] = item
        return item

    def __contains__(self, identifier: object) -> bool:
        return identifier in self._items

    def __getitem__(self, identifier: UUID) -> TodoItem:
        return self._items[identifier]

    def __iter__(self) -> Iterator[TodoItem]:
        return iter(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    def transition(
        self,
        identifier: UUID,
        status: TodoStatus,
        *,
        timestamp: datetime | None = None,
    ) -> TodoItem:
        item = self._items[identifier]
        updated = item.with_status(status, timestamp=timestamp)
        self._items[identifier] = updated
        return updated

    def mark_completed(self, identifier: UUID, *, timestamp: datetime | None = None) -> TodoItem:
        return self.transition(identifier, TodoStatus.COMPLETED, timestamp=timestamp)

    def mark_in_progress(self, identifier: UUID, *, timestamp: datetime | None = None) -> TodoItem:
        return self.transition(identifier, TodoStatus.IN_PROGRESS, timestamp=timestamp)

    def reset(self, identifier: UUID, *, timestamp: datetime | None = None) -> TodoItem:
        return self.transition(identifier, TodoStatus.PENDING, timestamp=timestamp)

    def update_tags(self, identifier: UUID, tags: Iterable[str]) -> TodoItem:
        item = self._items[identifier]
        updated = item.with_tags(tags)
        self._items[identifier] = updated
        return updated

    def update_due_date(self, identifier: UUID, due_at: datetime | None) -> TodoItem:
        item = self._items[identifier]
        updated = item.with_due_date(due_at)
        self._items[identifier] = updated
        return updated

    def update_priority(self, identifier: UUID, priority: TodoPriority) -> TodoItem:
        item = self._items[identifier]
        updated = item.with_priority(priority)
        self._items[identifier] = updated
        return updated

    def remove(self, identifier: UUID) -> TodoItem:
        return self._items.pop(identifier)

    def query(
        self,
        *,
        status: TodoStatus | None = None,
        tag: str | None = None,
        priority: TodoPriority | None = None,
    ) -> tuple[TodoItem, ...]:
        results = []
        lowered_tag = tag.lower().strip() if tag is not None else None
        for item in self._items.values():
            if status is not None and item.status is not status:
                continue
            if lowered_tag is not None and lowered_tag not in item.tags:
                continue
            if priority is not None and item.priority is not priority:
                continue
            results.append(item)
        return tuple(results)

    def overdue(self, *, reference_time: datetime | None = None) -> tuple[TodoItem, ...]:
        now = _ensure_utc(reference_time) or datetime.now(UTC)
        overdue_items = [
            item
            for item in self._items.values()
            if item.due_at is not None and item.due_at < now and not item.status.is_completed
        ]
        overdue_items.sort(key=lambda item: item.due_at or now)
        return tuple(overdue_items)

    def statistics(self) -> TodoStatistics:
        pending = sum(1 for item in self._items.values() if item.status is TodoStatus.PENDING)
        in_progress = sum(
            1 for item in self._items.values() if item.status is TodoStatus.IN_PROGRESS
        )
        completed = sum(1 for item in self._items.values() if item.status is TodoStatus.COMPLETED)
        return TodoStatistics(
            total=len(self._items),
            pending=pending,
            in_progress=in_progress,
            completed=completed,
        )

    def export(self) -> tuple[Mapping[str, object], ...]:
        return tuple(item.to_payload() for item in self._items.values())

    def prioritised(
        self,
        *,
        include_completed: bool = False,
    ) -> tuple[TodoItem, ...]:
        """Return tasks ordered by urgency for focused backlogs."""

        def sort_key(item: TodoItem) -> tuple[bool, int, datetime, datetime]:
            due_at = item.due_at or datetime.max.replace(tzinfo=UTC)
            return (
                item.status.is_completed,
                -item.priority.weight,
                due_at,
                item.created_at,
            )

        candidates = (
            item
            for item in self._items.values()
            if include_completed or not item.status.is_completed
        )
        return tuple(sorted(candidates, key=sort_key))


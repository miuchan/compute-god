from __future__ import annotations

from datetime import UTC, datetime, timedelta

from compute_god.todo import TodoList, TodoStatus


def test_todo_add_and_complete_roundtrip() -> None:
    todo = TodoList()
    due = datetime.now(UTC) + timedelta(days=3)
    item = todo.add(
        "Implement todo list",
        description="Use the shiny new stack",
        due_at=due,
        tags=("Dev", "Backend", "dev"),
    )

    assert item.identifier in todo
    assert item.status is TodoStatus.PENDING
    assert item.due_at == due
    assert item.tags == ("dev", "backend")

    in_progress = todo.mark_in_progress(item.identifier)
    assert in_progress.started_at is not None
    assert in_progress.status is TodoStatus.IN_PROGRESS

    completed = todo.mark_completed(item.identifier)
    assert completed.status is TodoStatus.COMPLETED
    assert completed.completed_at is not None

    exported = todo.export()
    assert exported[0]["status"] == TodoStatus.COMPLETED.value
    assert exported[0]["tags"] == ["dev", "backend"]


def test_todo_statistics_and_filters() -> None:
    todo = TodoList()
    urgent = todo.add("Ship feature", tags=("urgent",))
    doc = todo.add("Write docs", tags=("docs", "writing"))
    qa = todo.add("QA", tags=("urgent", "qa"))

    todo.mark_in_progress(urgent.identifier)
    todo.mark_completed(doc.identifier)

    stats = todo.statistics()
    assert stats.total == 3
    assert stats.pending == 1
    assert stats.in_progress == 1
    assert stats.completed == 1
    assert stats.completion_ratio == 1 / 3

    urgent_tasks = todo.query(tag="URGENT")
    assert {task.identifier for task in urgent_tasks} == {urgent.identifier, qa.identifier}

    pending_tasks = todo.query(status=TodoStatus.PENDING)
    assert tuple(task.identifier for task in pending_tasks) == (qa.identifier,)


def test_todo_overdue_detection_and_mutators() -> None:
    todo = TodoList()
    now = datetime.now(UTC)
    late = todo.add("Fix regression", due_at=now - timedelta(hours=2), tags=("bugfix",))
    future = todo.add("Plan roadmap", due_at=now + timedelta(days=1))

    todo.update_tags(future.identifier, ("planning", "roadmap"))
    todo.update_due_date(future.identifier, now + timedelta(days=2))

    overdue = todo.overdue(reference_time=now)
    assert overdue == (late,)

    todo.mark_completed(late.identifier)
    assert todo.overdue(reference_time=now) == ()


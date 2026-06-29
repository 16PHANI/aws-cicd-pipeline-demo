"""In-memory task store.

This is intentionally not backed by a database. The point of this service
is to demonstrate the delivery pipeline (lint, test, container, CI/CD,
infra-as-code) around a small API, not to build a task manager. Swapping
this module for a Postgres- or DynamoDB-backed one would not touch any
route, test, or deployment file, which is the whole reason the storage
layer is isolated here behind a small class instead of a global dict.
"""

import itertools
import threading
from typing import Dict, List, Optional

VALID_STATUSES = {"todo", "in_progress", "done"}


class TaskNotFoundError(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class TaskStore:
    """Thread-safe in-memory store. One lock, simple and correct.

    Gunicorn runs multiple worker *processes*, not threads, so this lock
    only protects against concurrent requests inside a single worker. That
    tradeoff is fine for a demo service and is called out in the README
    rather than hidden.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: Dict[int, dict] = {}
        self._id_counter = itertools.count(1)

    def reset(self) -> None:
        with self._lock:
            self._tasks.clear()
            self._id_counter = itertools.count(1)

    def create(self, title: str, status: str = "todo") -> dict:
        title = (title or "").strip()
        if not title:
            raise ValidationError("title is required and cannot be blank")
        if len(title) > 200:
            raise ValidationError("title must be 200 characters or fewer")
        if status not in VALID_STATUSES:
            raise ValidationError(f"status must be one of {sorted(VALID_STATUSES)}")

        with self._lock:
            task_id = next(self._id_counter)
            task = {"id": task_id, "title": title, "status": status}
            self._tasks[task_id] = task
            return dict(task)

    def list(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[dict]:
        if limit < 1 or limit > 200:
            raise ValidationError("limit must be between 1 and 200")
        if offset < 0:
            raise ValidationError("offset must be 0 or greater")

        with self._lock:
            items = list(self._tasks.values())

        if status is not None:
            if status not in VALID_STATUSES:
                raise ValidationError(f"status must be one of {sorted(VALID_STATUSES)}")
            items = [t for t in items if t["status"] == status]

        items.sort(key=lambda t: t["id"])
        return [dict(t) for t in items[offset : offset + limit]]

    def get(self, task_id: int) -> dict:
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"task {task_id} not found")
        return dict(task)

    def update(
        self, task_id: int, title: Optional[str] = None, status: Optional[str] = None
    ) -> dict:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise TaskNotFoundError(f"task {task_id} not found")

            if title is not None:
                title = title.strip()
                if not title:
                    raise ValidationError("title cannot be blank")
                if len(title) > 200:
                    raise ValidationError("title must be 200 characters or fewer")
                task["title"] = title

            if status is not None:
                if status not in VALID_STATUSES:
                    raise ValidationError(f"status must be one of {sorted(VALID_STATUSES)}")
                task["status"] = status

            self._tasks[task_id] = task
            return dict(task)

    def delete(self, task_id: int) -> None:
        with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(f"task {task_id} not found")
            del self._tasks[task_id]

    def count(self) -> int:
        with self._lock:
            return len(self._tasks)

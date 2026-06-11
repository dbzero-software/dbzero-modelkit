"""Tag-based object locking utility backed by dbzero."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Type

import dbzero as db0


@db0.memo(id="/dbzero/dbzero-modelkit/ObjectLock")
class ObjectLock:
    """General-purpose lock that holds references to locked objects."""

    def __init__(
        self,
        locked_objects: Any | list[Any],
        duration: int = 300,
        *,
        prefix: str | None = None,
    ) -> None:
        db0.set_prefix(self, prefix)
        if not isinstance(locked_objects, list):
            locked_objects = [locked_objects]
        self.locked_objects = locked_objects
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=duration)
        db0.tags(*locked_objects).add("LOCKED")

    def unlock(self) -> None:
        """Remove the LOCKED tag from all locked objects."""
        db0.tags(*self.locked_objects).remove("LOCKED")

    def unlock_with_error(self, error_objects: Any | list[Any] | None = None) -> None:
        """Unlock objects and mark selected or all objects with ERROR."""
        if error_objects is None:
            error_targets = self.locked_objects
        elif isinstance(error_objects, list):
            error_targets = error_objects
        else:
            error_targets = [error_objects]

        self.unlock()
        if error_targets:
            db0.tags(*error_targets).add("ERROR")

    def select(self, obj_type: Type) -> Iterable:
        """Return locked objects that are instances of obj_type."""
        return filter(lambda obj: isinstance(obj, obj_type), self.locked_objects)

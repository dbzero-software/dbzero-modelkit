"""Active-window model primitives backed by dbzero indexes."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Optional

import dbzero as db0

from dbzero_modelkit.rpc_integration import rpc as db0_rpc
from dbzero_modelkit.time_utils import normalize_end, normalize_start


@db0.memo(no_default_tags=True)
class ActiveBase:
    """Base object for models that are active only within a period of time."""

    def __init__(
        self,
        active_from: datetime | date | None = None,
        expires_on: datetime | date | None = None,
    ) -> None:
        self.active_from = active_from
        self.expires_on = expires_on

    @property
    def active(self) -> bool:
        """Return whether this object is active at the current date and time."""
        return self.is_active()

    @db0.immutable
    def is_active(self, as_of: datetime | date | None = None) -> bool:
        """Return whether as_of is within the active period."""
        if not as_of:
            as_of = datetime.now()

        if isinstance(as_of, date) and not isinstance(as_of, datetime):
            as_of = datetime.combine(as_of, datetime.min.time())

        active_from_dt = normalize_start(self.active_from) if self.active_from is not None else None
        expires_on_dt = normalize_end(self.expires_on) if self.expires_on is not None else None

        if active_from_dt is None and expires_on_dt is None:
            return True

        if active_from_dt and as_of < active_from_dt:
            return False

        if expires_on_dt and as_of > expires_on_dt:
            return False

        return True

    @db0.immutable
    def expired(self, date_and_time: datetime) -> bool:
        """Return whether the object is expired at date_and_time."""
        return not self.is_active(date_and_time)

    @db0.immutable
    def overlaps(self, other: "ActiveBase") -> bool:
        """Return whether this active period overlaps another one."""
        start_self = normalize_start(self.active_from)
        end_self = normalize_end(self.expires_on)
        start_other = normalize_start(other.active_from)
        end_other = normalize_end(other.expires_on)
        return start_self <= end_other and start_other <= end_self

    @db0.immutable
    def is_adjacent(self, other: "ActiveBase", max_gap: timedelta = timedelta(0)) -> bool:
        """Return whether this period is adjacent to another one within max_gap."""
        if self.overlaps(other):
            return False

        start_self = normalize_start(self.active_from)
        end_self = normalize_end(self.expires_on)
        start_other = normalize_start(other.active_from)
        end_other = normalize_end(other.expires_on)

        if end_self < start_other:
            return start_other - end_self <= max_gap

        if end_other < start_self:
            return start_self - end_other <= max_gap

        return False

    @db0.immutable
    def can_merge(self, other: "ActiveBase", max_gap: timedelta = timedelta(0)) -> bool:
        """Return True when periods overlap or are adjacent within max_gap."""
        return self.overlaps(other) or self.is_adjacent(other, max_gap=max_gap)

    @db0.immutable
    def merge(
        self,
        other: "ActiveBase",
        max_gap: timedelta = timedelta(0),
    ) -> Optional[tuple[datetime | date | None, datetime | date | None]]:
        """Return merged active bounds or None when periods cannot be merged."""
        if not self.can_merge(other, max_gap=max_gap):
            return None

        if self.active_from is None or other.active_from is None:
            merged_active_from = None
        elif normalize_start(self.active_from) <= normalize_start(other.active_from):
            merged_active_from = self.active_from
        else:
            merged_active_from = other.active_from

        if self.expires_on is None or other.expires_on is None:
            merged_expires_on = None
        elif normalize_end(self.expires_on) >= normalize_end(other.expires_on):
            merged_expires_on = self.expires_on
        else:
            merged_expires_on = other.expires_on

        return merged_active_from, merged_expires_on


@db0.memo(no_default_tags=True)
class ActiveIndex:
    """Container indexing ActiveBase-compatible objects by active period."""

    def __init__(self) -> None:
        self.__ix_active_from = db0.index()
        self.__ix_expires_on = db0.index()

    @db0_rpc.remote
    def add(self, obj: ActiveBase) -> None:
        """Add an ActiveBase-compatible object to both active-window indexes."""
        self.__ix_active_from.add(obj.active_from, obj)
        self.__ix_expires_on.add(obj.expires_on, obj)

    @db0_rpc.remote
    def remove(self, obj: ActiveBase) -> None:
        """Remove an ActiveBase-compatible object from both active-window indexes."""
        self.__ix_active_from.remove(obj.active_from, obj)
        self.__ix_expires_on.remove(obj.expires_on, obj)

    def _update_db0_index_attr(
        self,
        db0_index: db0.index,
        obj: ActiveBase,
        property_name: str,
        value: datetime | date | None,
    ) -> None:
        """Update one indexed active-window attribute and reindex the object."""
        if not db0_index.sort(db0.find(obj), desc=True, null_first=True):
            raise RuntimeError("Given ActiveBase object doesn't exist in any index.")
        self.remove(obj)
        setattr(obj, property_name, value)
        self.add(obj)

    @db0_rpc.remote
    def update(self, obj: ActiveBase, **kwargs: datetime | date | None) -> None:
        """Change active-window attributes and update the corresponding indexes."""
        if "active_from" in kwargs:
            self._update_db0_index_attr(
                db0_index=self.__ix_active_from,
                obj=obj,
                property_name="active_from",
                value=kwargs["active_from"],
            )

        if "expires_on" in kwargs:
            self._update_db0_index_attr(
                db0_index=self.__ix_expires_on,
                obj=obj,
                property_name="expires_on",
                value=kwargs["expires_on"],
            )

    @db0.immutable
    def find(self, **kwargs: bool) -> Iterable:
        """Return all indexed objects sorted by a selected active-window index."""
        index_to_find, desc = self.__get_index_and_desc_from_kwargs(**kwargs)
        return index_to_find.sort(index_to_find.select(), desc=desc)

    @db0.immutable
    def find_active(
        self,
        as_of: datetime | date | None = None,
        sort: bool = True,
        **kwargs: bool,
    ) -> Iterable:
        """Find objects active at as_of."""
        if not as_of:
            as_of = datetime.now()
        index_to_find, desc = self.__get_index_and_desc_from_kwargs(**kwargs)
        query = (
            self.active_from_index.select(low=None, high=as_of, null_first=True),
            self.expires_on_index.select(low=as_of, high=None, null_first=False),
        )
        if sort:
            return index_to_find.sort(db0.find(query), desc=desc)

        return db0.find(query)

    @db0.immutable
    def find_active_between(
        self,
        from_date: datetime | date,
        to_date: Optional[datetime | date] = None,
        sort: bool = True,
        **kwargs: bool,
    ) -> Iterable:
        """Find objects active within the given date range."""
        index_to_find, desc = self.__get_index_and_desc_from_kwargs(**kwargs)
        query = (
            self.active_from_index.select(low=None, high=to_date, null_first=True),
            self.expires_on_index.select(low=from_date, high=None, null_first=False),
        )
        if sort:
            return index_to_find.sort(db0.find(query), desc=desc)
        return db0.find(query)

    @property
    def active_from_index(self):
        """Return the active_from dbzero index."""
        return self.__ix_active_from

    @property
    def expires_on_index(self):
        """Return the expires_on dbzero index."""
        return self.__ix_expires_on

    def __get_index_and_desc_from_kwargs(self, **kwargs: bool):
        """Return selected index and sort direction from keyword arguments."""
        index_to_find_dict = {
            "active_from": self.active_from_index,
            "expires_on": self.expires_on_index,
        }
        for key, db0_index in index_to_find_dict.items():
            if key in kwargs:
                return db0_index, kwargs[key]
        return self.expires_on_index, True

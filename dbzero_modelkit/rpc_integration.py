"""Optional dbzero RPC integration for shared model classes."""

from __future__ import annotations

import functools
from typing import Any


class _NoRpcAdapter:
    """No-op adapter used when db0_rpc is not installed."""

    @staticmethod
    def init(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def remote(func: Any = None, **_kwargs: Any) -> Any:
        if func is None:
            return lambda wrapped: wrapped
        return func


_NO_RPC_ADAPTER = _NoRpcAdapter()


@functools.lru_cache(None)
def _load_rpc() -> Any:
    try:
        import db0_rpc  # pylint: disable=import-outside-toplevel

        return db0_rpc
    except ModuleNotFoundError:
        return _NO_RPC_ADAPTER


rpc = _load_rpc()


def has_rpc() -> bool:
    """Return True when db0_rpc is available."""
    return rpc is not _NO_RPC_ADAPTER

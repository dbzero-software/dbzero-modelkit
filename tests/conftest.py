"""Reusable pytest fixtures for dbzero-modelkit tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import dbzero as db0
import pytest


@dataclass(frozen=True)
class Db0TestContext:
    """Information about an initialized dbzero test context."""

    path: Path


@pytest.fixture()
def db0_fixture(tmp_path: Path):
    """Provide an initialized dbzero connection for a test."""
    db0_path = tmp_path / "db0"
    db0.init(str(db0_path), read_write=True)
    db0.open("test_prefix", "rw")
    yield Db0TestContext(path=db0_path)
    db0.close()

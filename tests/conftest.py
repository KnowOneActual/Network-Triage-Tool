"""Pytest configuration and fixtures.

This file helps pytest discover and import modules from the src directory.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# Add src directory to Python path for pytest
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_socket(mocker: MockerFixture) -> Any:
    """Generic socket mock fixture."""
    mock = mocker.patch("socket.socket")
    return mock


@pytest.fixture
def mock_popen(mocker: MockerFixture) -> Any:
    """Generic subprocess.Popen mock fixture."""
    return mocker.patch("subprocess.Popen")


@pytest.fixture
def sample_ping_output_linux() -> str:
    """Sample ping output for Linux."""
    return """
PING google.com (142.250.185.46) 56(84) bytes of data.
64 bytes from lax17s28-in-f14.1e100.net (142.250.185.46): icmp_seq=1 ttl=119 time=15.123 ms
64 bytes from lax17s28-in-f14.1e100.net (142.250.185.46): icmp_seq=2 ttl=119 time=14.856 ms
64 bytes from lax17s28-in-f14.1e100.net (142.250.185.46): icmp_seq=3 ttl=119 time=16.234 ms
    """


@pytest.fixture
def sample_ping_output_windows() -> str:
    """Sample ping output for Windows."""
    return """
Reply from 8.8.8.8: bytes=32 time=20ms TTL=119
Reply from 8.8.8.8: bytes=32 time=19ms TTL=119
Reply from 8.8.8.8: bytes=32 time=21ms TTL=119
    """

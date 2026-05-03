import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from network_triage.linux.network_toolkit import NetworkTriageToolkit as LinuxToolkit
from network_triage.macos.network_toolkit import NetworkTriageToolkit as MacToolkit
from network_triage.shared.shared_toolkit import NetworkTriageToolkitBase


def test_base_health_check() -> None:
    base = NetworkTriageToolkitBase()
    health = base.health_check()
    assert health["status"] in ["healthy", "degraded"]
    assert "ping" in health["components"]
    assert "network" in health["components"]


@patch("platform.system", return_value="Darwin")
def test_mac_health_check(mock_platform: MagicMock) -> None:
    mac = MacToolkit()
    health = mac.health_check()
    assert "system_profiler" in health["components"]
    assert "networksetup" in health["components"]
    assert "scutil" in health["components"]


@patch("platform.system", return_value="Linux")
def test_linux_health_check(mock_platform: MagicMock) -> None:
    linux = LinuxToolkit()
    health = linux.health_check()
    assert "ip" in health["components"]
    assert "uname" in health["components"]

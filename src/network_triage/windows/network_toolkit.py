import platform
import socket

from ..shared.shared_toolkit import NetworkTriageToolkitBase


class NetworkTriageToolkit(NetworkTriageToolkitBase):
    """Windows-specific network troubleshooting functions."""

    def get_system_info(self) -> dict[str, str]:
        return {"OS": f"{platform.system()} {platform.release()} (Windows Support Pending)", "Hostname": socket.gethostname()}

    def get_ip_info(self) -> dict[str, str]:
        # Placeholder - Real implementation would use 'ipconfig' or WMI
        return {"Internal IP": "Pending", "Gateway": "Pending", "Public IP": "Pending"}

    def get_connection_details(self) -> dict[str, str]:
        # Placeholder - Real implementation would use PowerShell or netsh
        return {
            "Interface": "Pending",
            "Connection Type": "Windows Support Coming Soon",
            "Status": "Unknown",
            "IP Address": "0.0.0.0",  # noqa: S104
            "MAC Address": "00:00:00:00:00:00",
            "Speed": "N/A",
            "MTU": "N/A",
            "DNS Servers": "N/A",
        }

    def traceroute_test(self, host: str) -> str:
        return "Traceroute not yet implemented for Windows."

    def network_adapter_info(self) -> str:
        return "Adapter info not yet implemented for Windows."

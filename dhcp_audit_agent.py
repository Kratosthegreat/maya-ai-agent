from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SAFE_COMMAND_ALLOWLIST = {
    "windows": [
        "Get-DhcpServerv4Scope",
        "Get-DhcpServerv4Statistics",
        "Get-DhcpServerv4Lease",
        "Get-Service -Name DHCPServer",
    ],
    "linux": [
        "cat /etc/dhcp/dhcpd.conf",
        "journalctl -u isc-dhcp-server --since",
        "systemctl status isc-dhcp-server --no-pager",
    ],
}

BLOCKED_KEYWORDS = {
    "restart", "stop", "start", "set-", "add-", "remove-", "new-", "delete", "truncate", "chmod", "chown"
}

@dataclass
class AccessContext:
    requester: str
    approval_ticket: Optional[str] = None
    read_only_role: Optional[str] = None

@dataclass
class AuditResult:
    ok: bool
    generated_at: str
    server: str
    data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)

class DhcpAuditAgent:
    def __init__(self, server_name: str, platform: str):
        self.server_name = server_name
        self.platform = platform.lower()
        if self.platform not in ("windows", "linux"):
            raise ValueError("platform must be 'windows' or 'linux'")

    def _has_authorization(self, ctx: AccessContext) -> bool:
        return bool(ctx.approval_ticket and ctx.read_only_role)

    def _min_permissions(self) -> List[str]:
        if self.platform == "windows":
            return [
                "DHCP Users group membership (read-only)",
                "PowerShell remoting read access to DHCP cmdlets",
                "Event log read permission",
            ]
        return [
            "Read access to /etc/dhcp/dhcpd.conf",
            "Read access to isc-dhcp-server logs",
            "Permission to run systemctl status (read-only)",
        ]

    def validate_command(self, command: str) -> bool:
        lowered = command.lower()
        if any(token in lowered for token in BLOCKED_KEYWORDS):
            return False
        return any(command.startswith(c) for c in SAFE_COMMAND_ALLOWLIST[self.platform])

    def planned_read_only_commands(self) -> List[str]:
        return SAFE_COMMAND_ALLOWLIST[self.platform][:]

    def collect_details(self, ctx: AccessContext, source_data: Optional[Dict[str, Any]] = None) -> AuditResult:
        now = datetime.now(timezone.utc).isoformat()
        if not self._has_authorization(ctx):
            return AuditResult(
                ok=False,
                generated_at=now,
                server=self.server_name,
                warnings=[
                    "Insufficient permissions. No probing executed.",
                    "Permission bypass is disabled by policy.",
                ],
                required_permissions=self._min_permissions(),
            )

        payload = source_data or {}
        warnings: List[str] = []
        expected_keys = ["service_status", "scopes", "scope_utilization", "lease_count", "recent_warnings"]
        for key in expected_keys:
            if key not in payload:
                warnings.append(f"Missing field from read-only source: {key}")

        return AuditResult(
            ok=True,
            generated_at=now,
            server=self.server_name,
            data=payload,
            warnings=warnings,
            required_permissions=self._min_permissions(),
        )

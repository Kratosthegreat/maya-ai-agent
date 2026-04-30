from dhcp_audit_agent import AccessContext, DhcpAuditAgent

def test_denies_without_authorization():
    agent = DhcpAuditAgent(server_name="dhcp-1", platform="windows")
    result = agent.collect_details(AccessContext(requester="u1"))
    assert result.ok is False
    assert "Insufficient permissions" in result.warnings[0]

def test_accepts_authorized_read_only_data():
    agent = DhcpAuditAgent(server_name="dhcp-1", platform="linux")
    ctx = AccessContext(requester="u1", approval_ticket="CHG-123", read_only_role="dhcp_auditor")
    result = agent.collect_details(
        ctx,
        {
            "service_status": "active",
            "scopes": ["10.10.10.0/24"],
            "scope_utilization": {"10.10.10.0/24": 35},
            "lease_count": 88,
            "recent_warnings": [],
        },
    )
    assert result.ok is True
    assert result.data["lease_count"] == 88

def test_blocks_unsafe_commands():
    agent = DhcpAuditAgent(server_name="dhcp-1", platform="linux")
    assert not agent.validate_command("systemctl restart isc-dhcp-server")
    assert agent.validate_command("systemctl status isc-dhcp-server --no-pager")

"""Tests for HostnameCollector and SshCollector."""

from __future__ import annotations

from hudctl.collectors.hostname import HostnameCollector
from hudctl.collectors.ssh import SshCollector


def test_hostname_collector_splits_fqdn() -> None:
    data = HostnameCollector(gethostname=lambda: "box.example.com").collect()
    assert data["hostname"] == "box.example.com"
    assert data["short"] == "box"


def test_ssh_collector_inactive() -> None:
    data = SshCollector(environ={}).collect()
    assert data["active"] is False
    assert data["client_ip"] is None


def test_ssh_collector_from_connection() -> None:
    data = SshCollector(
        environ={"SSH_CONNECTION": "1.2.3.4 12345 5.6.7.8 22"}
    ).collect()
    assert data["active"] is True
    assert data["client_ip"] == "1.2.3.4"

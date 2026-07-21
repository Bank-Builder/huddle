"""Tests for DockerCollector and KubernetesCollector."""

from __future__ import annotations

from pathlib import Path

from hudctl.collectors.docker import DockerCollector
from hudctl.collectors.kubernetes import KubernetesCollector


def test_docker_collector_socket_and_container(tmp_path: Path) -> None:
    sock = tmp_path / "docker.sock"
    sock.write_text("", encoding="utf-8")
    dockerenv = tmp_path / ".dockerenv"
    dockerenv.write_text("", encoding="utf-8")
    data = DockerCollector(
        socket_path=sock,
        dockerenv_path=dockerenv,
        cgroup_path=tmp_path / "missing",
    ).collect()
    assert data["available"] is True
    assert data["in_container"] is True
    assert data["socket"] == str(sock)


def test_docker_collector_cgroup_hint(tmp_path: Path) -> None:
    cgroup = tmp_path / "cgroup"
    cgroup.write_text("1:name=systemd:/docker/abc\n", encoding="utf-8")
    data = DockerCollector(
        socket_path=tmp_path / "nope",
        dockerenv_path=tmp_path / "nope2",
        cgroup_path=cgroup,
    ).collect()
    assert data["available"] is False
    assert data["in_container"] is True


def test_kubernetes_collector_reads_context(tmp_path: Path) -> None:
    kube = tmp_path / "config"
    kube.write_text(
        "apiVersion: v1\ncurrent-context: prod-admin\nkind: Config\n",
        encoding="utf-8",
    )
    data = KubernetesCollector(
        environ={"HOME": str(tmp_path)},
        kubeconfig=kube,
    ).collect()
    assert data["available"] is True
    assert data["context"] == "prod-admin"
    assert data["in_cluster"] is False


def test_kubernetes_collector_in_cluster_without_kubeconfig(tmp_path: Path) -> None:
    data = KubernetesCollector(
        environ={"KUBERNETES_SERVICE_HOST": "10.0.0.1", "HOME": str(tmp_path)},
        kubeconfig=tmp_path / "missing",
    ).collect()
    assert data["available"] is False
    assert data["in_cluster"] is True

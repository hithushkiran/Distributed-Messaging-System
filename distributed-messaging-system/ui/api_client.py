from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests


@dataclass(frozen=True)
class NodeStatus:
    node_id: str
    state: str
    term: int
    leader: str | None
    healthy_nodes: list[str]
    http_port: int


@dataclass(frozen=True)
class MessageRecord:
    message_id: str
    sender: str
    content: str
    timestamp: float

    @property
    def display_time(self) -> str:
        try:
            return datetime.fromtimestamp(float(self.timestamp)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "Unknown time"


@dataclass(frozen=True)
class StorageSnapshot:
    http_port: int
    reachable: bool
    messages: list[MessageRecord]
    raw_payload: dict[str, Any] | None = None
    error: str = ""

    @property
    def count(self) -> int:
        return len(self.messages)


class ClusterApiClient:
    def __init__(self, timeout: float = 0.75):
        self.timeout = timeout

    def get_status(self, http_port: int) -> NodeStatus | None:
        url = f"http://127.0.0.1:{http_port}/status"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            return NodeStatus(
                node_id=str(payload.get("node_id", "unknown")),
                state=str(payload.get("state", "UNKNOWN")),
                term=int(payload.get("term", 0) or 0),
                leader=payload.get("leader"),
                healthy_nodes=list(payload.get("healthy_nodes", [])),
                http_port=http_port,
            )
        except Exception:
            return None

    def get_messages(self, http_port: int) -> list[MessageRecord]:
        return self.get_storage_snapshot(http_port).messages

    def get_storage_snapshot(self, http_port: int) -> StorageSnapshot:
        url = f"http://127.0.0.1:{http_port}/messages"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            records: list[MessageRecord] = []
            for item in payload.get("messages", []):
                records.append(
                    MessageRecord(
                        message_id=str(item.get("message_id", "")),
                        sender=str(item.get("sender", "")),
                        content=str(item.get("content", "")),
                        timestamp=float(item.get("timestamp", 0) or 0),
                    )
                )
            records.sort(key=lambda record: record.timestamp)
            return StorageSnapshot(
                http_port=http_port,
                reachable=True,
                messages=records,
                raw_payload=payload,
            )
        except Exception as exc:
            return StorageSnapshot(
                http_port=http_port,
                reachable=False,
                messages=[],
                raw_payload=None,
                error=str(exc),
            )

    def get_storage_snapshots(self, http_ports: list[int]) -> dict[int, StorageSnapshot]:
        if not http_ports:
            return {}

        snapshots: dict[int, StorageSnapshot] = {}
        with ThreadPoolExecutor(max_workers=len(http_ports)) as executor:
            futures = {executor.submit(self.get_storage_snapshot, port): port for port in http_ports}
            for future in as_completed(futures):
                port = futures[future]
                try:
                    snapshots[port] = future.result()
                except Exception as exc:
                    snapshots[port] = StorageSnapshot(
                        http_port=port,
                        reachable=False,
                        messages=[],
                        raw_payload=None,
                        error=str(exc),
                    )

        return {port: snapshots[port] for port in http_ports}

    def get_cluster_snapshot(self, http_ports: list[int]) -> list[NodeStatus]:
        if not http_ports:
            return []

        statuses_by_port: dict[int, NodeStatus] = {}
        with ThreadPoolExecutor(max_workers=len(http_ports)) as executor:
            futures = {executor.submit(self.get_status, port): port for port in http_ports}
            for future in as_completed(futures):
                port = futures[future]
                try:
                    status = future.result()
                except Exception:
                    status = None
                if status is not None:
                    statuses_by_port[port] = status

        return [statuses_by_port[port] for port in http_ports if port in statuses_by_port]

    def discover_leader(self, http_ports: list[int]) -> tuple[int | None, NodeStatus | None]:
        for port in http_ports:
            status = self.get_status(port)
            if status and status.state.upper() == "LEADER":
                return port, status
        return None, None

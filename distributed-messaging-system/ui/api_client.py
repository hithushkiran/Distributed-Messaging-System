from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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


class ClusterApiClient:
    def __init__(self, timeout: float = 2.5):
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
            return records
        except Exception:
            return []

    def get_cluster_snapshot(self, http_ports: list[int]) -> list[NodeStatus]:
        statuses: list[NodeStatus] = []
        for port in http_ports:
            status = self.get_status(port)
            if status is not None:
                statuses.append(status)
        return statuses

    def discover_leader(self, http_ports: list[int]) -> tuple[int | None, NodeStatus | None]:
        for port in http_ports:
            status = self.get_status(port)
            if status and status.state.upper() == "LEADER":
                return port, status
        return None, None

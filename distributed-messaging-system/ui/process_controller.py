from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import signal
import subprocess
import sys
from typing import Optional


@dataclass(frozen=True)
class NodeRuntime:
    node_id: int
    port: int
    http_port: int
    process: subprocess.Popen | None
    log_file: Path
    log_handle: object | None = None

    @property
    def pid(self) -> int | None:
        return None if self.process is None else self.process.pid


class ProcessController:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = self.project_root / "src"
        self.runtime_dir = self.project_root / "ui" / "runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.nodes: dict[int, NodeRuntime] = {}

    def _server_command(self, node_id: int) -> list[str]:
        script = self.src_dir / "server_cluster.py"
        return [sys.executable, str(script), str(node_id)]

    def _node_ports(self, node_id: int) -> tuple[int, int]:
        base_port = 5000 + node_id
        return base_port, base_port + 100

    def start_node(self, node_id: int) -> NodeRuntime:
        existing = self.nodes.get(node_id)
        if existing and existing.process and existing.process.poll() is None:
            return existing

        port, http_port = self._node_ports(node_id)
        log_file = self.runtime_dir / f"node_{node_id}.log"
        log_handle = open(log_file, "a", encoding="utf-8")
        process = subprocess.Popen(
            self._server_command(node_id),
            cwd=self.src_dir,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        runtime = NodeRuntime(node_id=node_id, port=port, http_port=http_port, process=process, log_file=log_file, log_handle=log_handle)
        self.nodes[node_id] = runtime
        return runtime

    def stop_node(self, node_id: int) -> bool:
        runtime = self.nodes.get(node_id)
        if runtime is None or runtime.process is None:
            return False

        process = runtime.process
        if process.poll() is not None:
            return True

        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True)
            else:
                process.send_signal(signal.SIGTERM)
        except Exception:
            try:
                process.kill()
            except Exception:
                return False
        return True

    def restart_node(self, node_id: int) -> NodeRuntime:
        self.stop_node(node_id)
        return self.start_node(node_id)

    def is_running(self, node_id: int) -> bool:
        runtime = self.nodes.get(node_id)
        return bool(runtime and runtime.process and runtime.process.poll() is None)

    def get_log_tail(self, node_id: int, max_lines: int = 120) -> str:
        runtime = self.nodes.get(node_id)
        if runtime is None or not runtime.log_file.exists():
            return ""

        try:
            lines = runtime.log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            return "\n".join(lines[-max_lines:])
        except Exception:
            return ""

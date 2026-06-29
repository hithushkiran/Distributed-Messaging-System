from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import signal
import socket
import subprocess
import sys
import time


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

    def _is_port_open(self, port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.4):
                return True
        except OSError:
            return False

    def _stop_external_node_processes(self, node_id: int) -> bool:
        if os.name != "nt":
            return False

        pattern = rf'server_cluster\.py"?\s+{node_id}(\s|$)'
        command = (
            f"$pattern = '{pattern}'; "
            "$targets = Get-CimInstance Win32_Process -Filter \"name = 'python.exe'\" | "
            "Where-Object { $_.CommandLine -and $_.CommandLine -like '*server_cluster.py*' -and "
            "$_.CommandLine -match $pattern }; "
            "$targets | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; "
            "if ($targets) { 'stopped' }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                check=False,
                capture_output=True,
                text=True,
                timeout=2.5,
            )
        except subprocess.TimeoutExpired:
            return False
        return result.returncode == 0 and bool(result.stdout.strip())

    def _stop_owned_process(self, process: subprocess.Popen) -> bool:
        if process.poll() is not None:
            return True

        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    check=False,
                    capture_output=True,
                    timeout=2.5,
                )
            else:
                process.send_signal(signal.SIGTERM)
            return True
        except Exception:
            try:
                process.kill()
                return True
            except Exception:
                return False

    def _close_log_handle(self, runtime: NodeRuntime | None) -> None:
        if runtime is None or runtime.log_handle is None:
            return

        try:
            runtime.log_handle.close()
        except Exception:
            pass

    def _wait_for_ports_closed(self, node_id: int, attempts: int = 5) -> bool:
        port, http_port = self._node_ports(node_id)
        for _ in range(attempts):
            if not self._is_port_open(port) and not self._is_port_open(http_port):
                return True
            time.sleep(0.25)
        return not self._is_port_open(port) and not self._is_port_open(http_port)

    def start_node(self, node_id: int) -> NodeRuntime:
        existing = self.nodes.get(node_id)
        if existing and existing.process and existing.process.poll() is None:
            return existing

        port, http_port = self._node_ports(node_id)
        log_file = self.runtime_dir / f"node_{node_id}.log"

        if self._is_port_open(port) or self._is_port_open(http_port):
            runtime = NodeRuntime(node_id=node_id, port=port, http_port=http_port, process=None, log_file=log_file)
            self.nodes[node_id] = runtime
            return runtime

        log_handle = open(log_file, "a", encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        process = subprocess.Popen(
            self._server_command(node_id),
            cwd=self.src_dir,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            env=env,
        )
        runtime = NodeRuntime(node_id=node_id, port=port, http_port=http_port, process=process, log_file=log_file, log_handle=log_handle)
        self.nodes[node_id] = runtime
        time.sleep(0.35)
        if process.poll() is not None:
            try:
                log_handle.close()
            except Exception:
                pass
        return runtime

    def stop_node(self, node_id: int) -> bool:
        runtime = self.nodes.get(node_id)
        stopped = False

        if runtime is not None and runtime.process is not None:
            stopped = self._stop_owned_process(runtime.process)

        external_stopped = self._stop_external_node_processes(node_id)
        self._close_log_handle(runtime)
        self.nodes.pop(node_id, None)
        ports_closed = self._wait_for_ports_closed(node_id)
        return stopped or external_stopped or ports_closed

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

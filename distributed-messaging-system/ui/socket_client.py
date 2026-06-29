from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class SendResult:
    ok: bool
    detail: str


class SocketChatClient:
    protocol_version = 2

    def __init__(self, timeout: float = 1.5):
        self.timeout = timeout
        self.protocol_version = self.__class__.protocol_version
        self.socket: socket.socket | None = None
        self.username: str | None = None
        self.server: tuple[str, int] | None = None

    def _send_payload(self, payload: dict) -> None:
        self.socket.sendall(json.dumps(payload).encode("utf-8"))

    def _wait_for_login_ack(self) -> bool:
        if self.socket is None:
            return False

        previous_timeout = self.socket.gettimeout()
        try:
            self.socket.settimeout(self.timeout)
            data = self.socket.recv(4096)
            return bool(data)
        except socket.timeout:
            return False
        except Exception:
            self.close()
            return False
        finally:
            if self.socket is not None:
                self.socket.settimeout(previous_timeout)

    def connect(self, host: str, port: int, username: str) -> SendResult:
        self.close()
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((host, port))
            self.server = (host, port)
            self.username = username
            payload = {
                "type": "login",
                "sender": username,
                "content": f"{username} has joined the chat",
                "timestamp": time.time(),
            }
            self._send_payload(payload)
            if not self._wait_for_login_ack():
                self.close()
                return SendResult(False, "Login was not acknowledged by the server")
            return SendResult(True, f"Connected to {host}:{port} as {username}")
        except Exception as exc:
            self.close()
            return SendResult(False, f"Connection failed: {exc}")

    def send_chat(self, content: str) -> SendResult:
        if self.socket is None or self.server is None or self.username is None:
            return SendResult(False, "Not connected")

        try:
            payload = {
                "type": "chat",
                "sender": self.username,
                "content": content,
                "timestamp": time.time(),
            }
            self._send_payload(payload)
            return SendResult(True, "Message sent")
        except Exception as exc:
            self.close()
            return SendResult(False, f"Send failed: {exc}")

    def logout(self) -> SendResult:
        if self.socket is None or self.username is None:
            self.close()
            return SendResult(True, "Already disconnected")

        try:
            payload = {
                "type": "logout",
                "sender": self.username,
                "content": f"{self.username} has left the chat",
                "timestamp": time.time(),
            }
            self._send_payload(payload)
            self.close()
            return SendResult(True, "Disconnected")
        except Exception as exc:
            self.close()
            return SendResult(False, f"Logout failed: {exc}")

    def close(self) -> None:
        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass
        self.socket = None
        self.server = None
        self.username = None

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
import sys
import time
from typing import Iterable

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.api_client import ClusterApiClient, MessageRecord, NodeStatus, StorageSnapshot
from ui.process_controller import ProcessController
from ui.socket_client import SocketChatClient

NODE_DEFS = [
    {"node_id": 0, "port": 5000, "http_port": 5100},
    {"node_id": 1, "port": 5001, "http_port": 5101},
    {"node_id": 2, "port": 5002, "http_port": 5102},
]
CHAT_CLIENT_PROTOCOL_VERSION = 2


def init_state() -> None:
    st.session_state.setdefault("controller", ProcessController(PROJECT_ROOT))
    if getattr(st.session_state.get("api_client"), "timeout", None) != 0.75:
        st.session_state.api_client = ClusterApiClient(timeout=0.75)
    chat_client = st.session_state.get("chat_client")
    if getattr(chat_client, "timeout", None) != 1.5 or getattr(chat_client, "protocol_version", None) != CHAT_CLIENT_PROTOCOL_VERSION:
        old_client = st.session_state.get("chat_client")
        if old_client is not None:
            old_client.close()
        st.session_state.chat_client = SocketChatClient(timeout=1.5)
    st.session_state.setdefault("selected_node", 0)
    st.session_state.setdefault("status_message", "Ready")
    st.session_state.setdefault("last_action", "")
    st.session_state.setdefault("username", "Alice")
    st.session_state.setdefault("message_text", "Hello distributed world!")
    st.session_state.setdefault("auto_refresh", False)


def css_block() -> str:
    return """
    <style>
        :root {
            --bg: #eaf4ff;
            --panel: rgba(255, 255, 255, 0.9);
            --panel-strong: rgba(255, 255, 255, 0.96);
            --panel-soft: rgba(232, 244, 255, 0.84);
            --line: rgba(59, 130, 246, 0.24);
            --text: #0f172a;
            --muted: #526579;
            --accent: #075985;
            --accent-2: #2563eb;
            --accent-soft: #dbeafe;
            --ink-panel: #0b2a4a;
            --danger: #dc2626;
            --danger-soft: #fee2e2;
            --warning: #b45309;
            --warning-soft: #fef3c7;
            --success: #15803d;
            --success-soft: #dcfce7;
        }
        .stApp {
            background:
                linear-gradient(145deg, rgba(9, 60, 120, 0.16) 0%, rgba(37, 99, 235, 0.10) 28%, rgba(14, 165, 233, 0.12) 58%, rgba(248, 250, 252, 0.98) 100%),
                linear-gradient(180deg, #eff7ff 0%, #dbeafe 42%, #f8fbff 100%);
            color: var(--text);
            font-family: Inter, Segoe UI, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
        }
        .hero {
            position: relative;
            overflow: hidden;
            padding: 1.25rem 1.35rem;
            border: 1px solid rgba(147, 197, 253, 0.34);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(8, 47, 73, 0.96), rgba(12, 74, 110, 0.92) 45%, rgba(30, 64, 175, 0.88));
            box-shadow: 0 22px 60px rgba(15, 23, 42, 0.18);
            margin-bottom: 1.05rem;
        }
        .hero::after {
            content: "";
            position: absolute;
            inset: auto -12% -42% 32%;
            height: 180px;
            background: linear-gradient(90deg, rgba(125, 211, 252, 0.28), rgba(191, 219, 254, 0.08));
            transform: rotate(-8deg);
        }
        .hero h1 {
            position: relative;
            z-index: 1;
            margin: 0;
            font-size: 2.15rem;
            font-weight: 800;
            letter-spacing: 0;
            color: #f8fafc;
        }
        .hero-kicker {
            position: relative;
            z-index: 1;
            margin-bottom: 0.35rem;
            color: #bae6fd;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .hero p {
            position: relative;
            z-index: 1;
            margin: 0.5rem 0 0;
            color: #dbeafe;
            font-size: 0.98rem;
            line-height: 1.5;
            max-width: 980px;
        }
        .hero-badges {
            position: relative;
            z-index: 1;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.9rem;
        }
        .metric-card {
            position: relative;
            overflow: hidden;
            min-height: 104px;
            padding: 0.95rem 1rem;
            border-radius: 8px;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(239, 246, 255, 0.84));
            border: 1px solid var(--line);
            box-shadow: 0 16px 36px rgba(30, 64, 175, 0.10);
            backdrop-filter: blur(10px);
        }
        .metric-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #38bdf8, #2563eb, #0f766e);
        }
        .metric-label {
            color: #42617d;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.35rem;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 800;
            color: #0b2a4a;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }
        .metric-subtext {
            color: var(--muted);
            font-size: 0.84rem;
            margin-top: 0.35rem;
            line-height: 1.35;
        }
        .panel {
            padding: 1rem 1.05rem;
            border-radius: 8px;
            border: 1px solid var(--line);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.86));
            box-shadow: 0 16px 38px rgba(30, 64, 175, 0.09);
            backdrop-filter: blur(10px);
        }
        .panel-title {
            margin: 0 0 0.55rem;
            font-size: 1.02rem;
            font-weight: 800;
            color: #0b2a4a;
        }
        .node-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.28rem 0.68rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .node-pill.running { background: var(--success-soft); color: var(--success); border-color: #bbf7d0; }
        .node-pill.stopped { background: var(--danger-soft); color: var(--danger); border-color: #fecaca; }
        .node-pill.leader { background: var(--accent-soft); color: var(--accent); border-color: #99f6e4; }
        .node-pill.follower { background: #eef2ff; color: #3730a3; border-color: #c7d2fe; }
        .node-pill.warning { background: var(--warning-soft); color: var(--warning); border-color: #fde68a; }
        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(8, 47, 73, 0.98), rgba(12, 74, 110, 0.96));
            border-right: 1px solid rgba(125, 211, 252, 0.26);
        }
        section[data-testid="stSidebar"] * {
            color: #e0f2fe;
        }
        section[data-testid="stSidebar"] .stCaptionContainer,
        section[data-testid="stSidebar"] p {
            color: #bae6fd;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
            color: #f8fafc;
        }
        .tiny-label {
            color: #60758c;
            font-size: 0.82rem;
        }
        .msg-row {
            padding: 0.82rem 0.9rem;
            border: 1px solid var(--line);
            border-radius: 8px;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(239, 246, 255, 0.74));
            box-shadow: 0 10px 24px rgba(30, 64, 175, 0.07);
            margin-bottom: 0.55rem;
        }
        .msg-header {
            display: flex;
            justify-content: space-between;
            gap: 0.6rem;
            font-size: 0.8rem;
            color: var(--muted);
            margin-bottom: 0.35rem;
            flex-wrap: wrap;
        }
        .msg-content {
            font-size: 0.96rem;
            color: var(--text);
            white-space: pre-wrap;
            line-height: 1.45;
            overflow-wrap: anywhere;
        }
        .footer-note {
            color: var(--muted);
            font-size: 0.82rem;
            margin: 0.45rem 0 0.75rem;
        }
        .status-strip {
            padding: 0.95rem 1rem;
            border-radius: 8px;
            border: 1px solid var(--line);
            background:
                linear-gradient(90deg, rgba(255, 255, 255, 0.94), rgba(219, 234, 254, 0.78));
            box-shadow: 0 14px 32px rgba(37, 99, 235, 0.09);
            margin-bottom: 0.9rem;
        }
        div[data-testid="stTabs"] button {
            color: #24435f;
            font-weight: 750;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #075985;
        }
        div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            background: linear-gradient(90deg, #38bdf8, #2563eb);
            height: 3px;
        }
        div.stButton > button {
            border-radius: 8px;
            border: 1px solid rgba(125, 211, 252, 0.42);
            background: rgba(255, 255, 255, 0.12);
            color: #f8fafc;
            font-weight: 800;
        }
        div.stButton > button:hover {
            border-color: #7dd3fc;
            background: rgba(14, 165, 233, 0.22);
            color: #ffffff;
        }
        div[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #0ea5e9, #2563eb);
            border-color: transparent;
            color: #ffffff;
        }
        input, textarea {
            border-radius: 8px !important;
            color: #0f172a !important;
            background: #ffffff !important;
        }
        input::placeholder, textarea::placeholder {
            color: #64748b !important;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 12px 28px rgba(30, 64, 175, 0.08);
        }
        pre {
            border-radius: 8px !important;
            border: 1px solid rgba(96, 165, 250, 0.24) !important;
        }
        .explain-hero {
            padding: 1.15rem 1.25rem;
            border-radius: 8px;
            border: 1px solid rgba(125, 211, 252, 0.28);
            background: linear-gradient(135deg, rgba(8, 47, 73, 0.96), rgba(30, 64, 175, 0.9));
            box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
            margin-bottom: 1rem;
        }
        .explain-hero h2 {
            color: #f8fafc;
            margin: 0;
            font-size: 1.65rem;
            letter-spacing: 0;
        }
        .explain-hero p {
            color: #dbeafe;
            margin: 0.45rem 0 0;
            line-height: 1.55;
        }
        .explain-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 0.85rem 0 1rem;
        }
        .explain-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(239, 246, 255, 0.82));
            box-shadow: 0 14px 32px rgba(30, 64, 175, 0.08);
            padding: 1rem;
            min-height: 128px;
        }
        .explain-card h3, .diagram-panel h3 {
            margin: 0 0 0.45rem;
            color: #0b2a4a;
            font-size: 1rem;
            font-weight: 850;
        }
        .explain-card p, .diagram-panel p {
            margin: 0;
            color: #526579;
            font-size: 0.9rem;
            line-height: 1.48;
        }
        .diagram-panel {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 16px 38px rgba(30, 64, 175, 0.08);
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .arch-map {
            display: grid;
            grid-template-columns: 1fr 0.35fr 1.6fr;
            gap: 0.75rem;
            align-items: stretch;
            margin-top: 0.85rem;
        }
        .diagram-box {
            border: 1px solid rgba(96, 165, 250, 0.32);
            border-radius: 8px;
            background: linear-gradient(180deg, #ffffff, #eff6ff);
            padding: 0.8rem;
            color: #0f172a;
        }
        .diagram-box.dark {
            background: linear-gradient(180deg, #0b2a4a, #075985);
            color: #f8fafc;
            border-color: rgba(125, 211, 252, 0.32);
        }
        .diagram-title {
            font-weight: 850;
            margin-bottom: 0.35rem;
        }
        .diagram-small {
            color: inherit;
            opacity: 0.78;
            font-size: 0.82rem;
            line-height: 1.38;
        }
        .arrow-box {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #075985;
            font-weight: 900;
            font-size: 1.6rem;
        }
        .node-stack {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.65rem;
        }
        .node-box {
            border: 1px solid rgba(37, 99, 235, 0.22);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.72);
            padding: 0.65rem;
        }
        .node-box strong {
            color: #075985;
        }
        .node-box ul {
            padding-left: 1rem;
            margin: 0.45rem 0 0;
            color: #526579;
            font-size: 0.82rem;
            line-height: 1.4;
        }
        .flow-track {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.85rem;
        }
        .flow-step {
            position: relative;
            border: 1px solid rgba(96, 165, 250, 0.28);
            border-radius: 8px;
            background: linear-gradient(180deg, #ffffff, #eff6ff);
            padding: 0.85rem;
            min-height: 142px;
        }
        .step-num {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.55rem;
            height: 1.55rem;
            border-radius: 999px;
            background: linear-gradient(135deg, #0ea5e9, #2563eb);
            color: #ffffff;
            font-size: 0.82rem;
            font-weight: 900;
            margin-bottom: 0.55rem;
        }
        .flow-step h4 {
            margin: 0 0 0.35rem;
            color: #0b2a4a;
            font-size: 0.92rem;
        }
        .flow-step p {
            margin: 0;
            color: #526579;
            font-size: 0.82rem;
            line-height: 1.38;
        }
        .state-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.85rem;
        }
        .state-card {
            border-radius: 8px;
            padding: 0.9rem;
            color: #f8fafc;
            background: linear-gradient(135deg, #0f172a, #075985);
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.14);
        }
        .state-card h4 {
            margin: 0 0 0.35rem;
            color: #f8fafc;
            font-size: 0.98rem;
        }
        .state-card p {
            color: #dbeafe;
            font-size: 0.84rem;
        }
        .timeline {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.85rem;
        }
        .timeline-card {
            border-left: 4px solid #0ea5e9;
            border-radius: 8px;
            background: #ffffff;
            padding: 0.8rem;
            box-shadow: 0 12px 28px rgba(30, 64, 175, 0.07);
        }
        .timeline-card strong {
            color: #0b2a4a;
        }
        .timeline-card p {
            margin-top: 0.35rem;
            font-size: 0.82rem;
        }
        .matrix {
            display: grid;
            grid-template-columns: 1fr 1.2fr 1.2fr;
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
            margin-top: 0.85rem;
        }
        .matrix div {
            padding: 0.72rem 0.8rem;
            border-bottom: 1px solid rgba(96, 165, 250, 0.18);
            border-right: 1px solid rgba(96, 165, 250, 0.18);
            background: rgba(255, 255, 255, 0.72);
            color: #526579;
            font-size: 0.86rem;
            line-height: 1.38;
        }
        .matrix div:nth-child(3n) {
            border-right: 0;
        }
        .matrix .head {
            background: linear-gradient(135deg, #0b2a4a, #075985);
            color: #f8fafc;
            font-weight: 850;
        }
        .matrix .name {
            color: #0b2a4a;
            font-weight: 850;
        }
        @media (max-width: 900px) {
            .explain-grid, .node-stack, .flow-track, .state-grid, .timeline, .arch-map {
                grid-template-columns: 1fr;
            }
            .arrow-box {
                min-height: 28px;
                transform: rotate(90deg);
            }
        }
    </style>
    """


def human_time(value: float) -> str:
    try:
        return datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "Unknown time"


def http_ports() -> list[int]:
    return [node["http_port"] for node in NODE_DEFS]


def node_for_http_port(http_port: int) -> dict[str, int]:
    return next(node for node in NODE_DEFS if node["http_port"] == http_port)


def status_class(status: NodeStatus | None, ui_managed: bool) -> str:
    if status is None:
        return "running" if ui_managed else "stopped"
    if status.state.upper() == "LEADER":
        return "leader"
    return "follower"


def render_metric(label: str, value: str, subtext: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(value)}</div>
            {f'<div class="metric-subtext">{escape(subtext)}</div>' if subtext else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_node_card(
    node_def: dict[str, int],
    status: NodeStatus | None,
    ui_managed: bool,
    storage: StorageSnapshot | None,
) -> None:
    pill_class = status_class(status, ui_managed)
    if status is None:
        pill_text = "Managed" if ui_managed else "Offline"
    else:
        pill_text = status.state.title()

    leader_text = status.leader if status and status.leader else "-"
    healthy_count = len(status.healthy_nodes) if status else 0
    storage_count = storage.count if storage and storage.reachable else 0
    process_label = "UI-managed" if ui_managed else ("Detected by HTTP" if status else "Not detected")
    st.markdown(
        f"""
        <div class="panel">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
                <div>
                    <div class="panel-title">Node {node_def['node_id']}</div>
                    <div class="tiny-label">TCP {node_def['port']} / HTTP {node_def['http_port']}</div>
                </div>
                <span class="node-pill {pill_class}">{escape(pill_text)}</span>
            </div>
            <div style="margin-top:0.85rem; display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:0.7rem;">
                <div>
                    <div class="tiny-label">Term</div>
                    <div style="font-size:1.08rem; font-weight:750;">{status.term if status else '-'}</div>
                </div>
                <div>
                    <div class="tiny-label">Leader</div>
                    <div style="font-size:0.98rem; font-weight:750; overflow-wrap:anywhere;">{escape(str(leader_text))}</div>
                </div>
                <div>
                    <div class="tiny-label">Healthy peers</div>
                    <div style="font-size:1.08rem; font-weight:750;">{healthy_count}</div>
                </div>
                <div>
                    <div class="tiny-label">Stored messages</div>
                    <div style="font-size:1.08rem; font-weight:750;">{storage_count}</div>
                </div>
            </div>
            <div class="footer-note">{escape(process_label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_statuses(api: ClusterApiClient) -> list[NodeStatus]:
    return api.get_cluster_snapshot(http_ports())


def get_leader_node(statuses: Iterable[NodeStatus]) -> NodeStatus | None:
    for status in statuses:
        if status.state.upper() == "LEADER":
            return status
    return None


def ensure_connection(statuses: list[NodeStatus]) -> str:
    leader = get_leader_node(statuses)
    if leader is None:
        st.session_state.chat_client.close()
        return "No leader available yet. Start the cluster and wait for election."

    username = st.session_state.username.strip()
    if not username:
        st.session_state.chat_client.close()
        return "Username is required."

    leader_port = int(leader.node_id.split(":")[-1])
    current_server = st.session_state.chat_client.server
    if current_server is None or current_server[1] != leader_port or st.session_state.chat_client.username != username:
        result = st.session_state.chat_client.connect("127.0.0.1", leader_port, username)
        return result.detail

    return f"Connected to leader on port {leader_port}."


def send_message_via_leader(statuses: list[NodeStatus], content: str) -> tuple[bool, str, NodeStatus | None]:
    leader = get_leader_node(statuses)
    if leader is None:
        st.session_state.chat_client.close()
        return False, "No leader available yet. Refresh or wait for election to settle.", None

    sender = st.session_state.username.strip()
    sent_at = time.time()
    connect_message = ensure_connection(statuses)
    if st.session_state.chat_client.socket is None:
        return False, connect_message, leader

    send_result = st.session_state.chat_client.send_chat(content)
    if send_result.ok:
        if wait_for_message_visible(st.session_state.api_client, sender, content, sent_at):
            return True, "Message sent and confirmed in storage", leader
        return False, "Message reached the socket, but it was not visible in storage yet", leader

    # A leader restart can leave Streamlit holding a stale socket. Re-discover and retry once.
    st.session_state.chat_client.close()
    retry_statuses = get_statuses(st.session_state.api_client)
    retry_leader = get_leader_node(retry_statuses)
    if retry_leader is None:
        return False, f"{send_result.detail}. No leader available after retry.", leader

    retry_connect = ensure_connection(retry_statuses)
    if st.session_state.chat_client.socket is None:
        return False, retry_connect, retry_leader

    retry_result = st.session_state.chat_client.send_chat(content)
    if not retry_result.ok:
        return False, retry_result.detail, retry_leader
    if wait_for_message_visible(st.session_state.api_client, sender, content, sent_at):
        return True, "Message sent after reconnect and confirmed in storage", retry_leader
    return False, "Message reached the socket after reconnect, but it was not visible in storage yet", retry_leader


def wait_for_message_visible(api: ClusterApiClient, sender: str, content: str, sent_at: float, timeout: float = 2.5) -> bool:
    deadline = time.monotonic() + timeout
    min_timestamp = sent_at - 3.0

    while time.monotonic() < deadline:
        snapshots = api.get_storage_snapshots(http_ports())
        for snapshot in snapshots.values():
            for message in snapshot.messages:
                if message.sender == sender and message.content == content and message.timestamp >= min_timestamp:
                    return True
        time.sleep(0.25)

    return False


def render_message_feed(messages: list[MessageRecord]) -> None:
    if not messages:
        st.info("No messages available yet. Send one from the chat panel.")
        return

    for message in messages[-100:]:
        sender = escape(message.sender or "SYSTEM")
        message_id = escape(message.message_id)
        content = escape(message.content)
        st.markdown(
            f"""
            <div class="msg-row">
                <div class="msg-header">
                    <span><strong>{sender}</strong> / {message_id}</span>
                    <span>{human_time(message.timestamp)}</span>
                </div>
                <div class="msg-content">{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_log_tail(controller: ProcessController, node_id: int) -> None:
    log_tail = controller.get_log_tail(node_id)
    if not log_tail:
        st.caption("No log output captured yet for nodes started from this UI.")
        return
    st.code(log_tail, language="text")


def message_table_rows(messages: list[MessageRecord]) -> list[dict[str, str]]:
    return [
        {
            "message_id": message.message_id,
            "sender": message.sender or "SYSTEM",
            "content": message.content,
            "timestamp": human_time(message.timestamp),
        }
        for message in messages
    ]


def storage_consistency_summary(snapshots: dict[int, StorageSnapshot]) -> tuple[str, str, str]:
    reachable = [snapshot for snapshot in snapshots.values() if snapshot.reachable]
    if not reachable:
        return "No storage APIs reachable", "Start the cluster, then refresh the dashboard.", "stopped"
    if len(reachable) == 1:
        snapshot = reachable[0]
        return (
            "Only one node reachable",
            f"Node on HTTP {snapshot.http_port} has {snapshot.count} stored messages.",
            "warning",
        )

    id_sets = {snapshot.http_port: {message.message_id for message in snapshot.messages} for snapshot in reachable}
    reference = next(iter(id_sets.values()))
    if all(message_ids == reference for message_ids in id_sets.values()):
        return "Storage is consistent", "All reachable nodes report the same message IDs.", "leader"

    counts = ", ".join(f"{port}: {len(ids)}" for port, ids in id_sets.items())
    return "Storage differs between nodes", f"Message ID counts by HTTP port: {counts}", "warning"


def render_storage_inspector(snapshots: dict[int, StorageSnapshot]) -> None:
    title, detail, pill_class = storage_consistency_summary(snapshots)
    st.markdown(
        f"""
        <div class="status-strip">
            <span class="node-pill {pill_class}">{escape(title)}</span>
            <span style="margin-left:0.65rem; color:var(--muted);">{escape(detail)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for idx, node in enumerate(NODE_DEFS):
        snapshot = snapshots[node["http_port"]]
        with cols[idx]:
            st.markdown(
                f"""
                <div class="panel">
                    <div class="panel-title">Node {node['node_id']} Storage</div>
                    <div class="tiny-label">GET http://127.0.0.1:{node['http_port']}/messages</div>
                    <div style="margin-top:0.75rem;">
                        <span class="node-pill {'running' if snapshot.reachable else 'stopped'}">
                            {'Reachable' if snapshot.reachable else 'Unreachable'}
                        </span>
                        <span style="margin-left:0.55rem; font-weight:750;">{snapshot.count} messages</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if snapshot.error:
                st.caption(snapshot.error)
            if snapshot.messages:
                st.dataframe(message_table_rows(snapshot.messages), use_container_width=True, hide_index=True)
            else:
                st.info("No stored messages returned by this node.")

            with st.expander(f"Raw JSON from Node {node['node_id']}"):
                if snapshot.raw_payload is None:
                    st.caption("No JSON payload available.")
                else:
                    st.json(snapshot.raw_payload)


def render_system_explainer() -> None:
    st.markdown(
        """
        <div class="explain-hero">
            <h2>System Explained</h2>
            <p>
                This page explains the implementation behind the demo: a three-node messaging
                cluster with manual Raft consensus, leader-only replicated storage, health-based
                failover monitoring, synchronized timestamps, and HTTP visibility for the UI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="explain-grid">
            <div class="explain-card">
                <h3>Cluster model</h3>
                <p>Three Python server processes run on TCP ports 5000, 5001, and 5002. Each process owns its own Raft node, message store, failover monitor, time sync component, and HTTP query API.</p>
            </div>
            <div class="explain-card">
                <h3>Consistency rule</h3>
                <p>Only the current Raft leader initiates writes into replicated storage. A message becomes safe after the leader replicates the log entry to a majority of nodes.</p>
            </div>
            <div class="explain-card">
                <h3>Fault tolerance</h3>
                <p>With three nodes, quorum is two. The system can survive one node failure while still electing a leader and committing new messages through the remaining majority.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="diagram-panel">
            <h3>1. Runtime architecture</h3>
            <p>The Streamlit app is a control and inspection layer. It starts existing server processes, sends chat messages through the socket protocol, and reads status/storage through the existing HTTP APIs.</p>
            <div class="arch-map">
                <div class="diagram-box dark">
                    <div class="diagram-title">Client surfaces</div>
                    <div class="diagram-small">
                        Streamlit UI<br>
                        Terminal client<br>
                        Manual HTTP queries
                    </div>
                </div>
                <div class="arrow-box">-&gt;</div>
                <div class="node-stack">
                    <div class="node-box">
                        <strong>Node 0</strong><br>
                        <span class="diagram-small">TCP 5000 / HTTP 5100 / Raft RPC 6000</span>
                        <ul>
                            <li>ClusterServer</li>
                            <li>Consensus + RaftNode</li>
                            <li>MessageStorage</li>
                            <li>Failover + TimeSync</li>
                        </ul>
                    </div>
                    <div class="node-box">
                        <strong>Node 1</strong><br>
                        <span class="diagram-small">TCP 5001 / HTTP 5101 / Raft RPC 6001</span>
                        <ul>
                            <li>ClusterServer</li>
                            <li>Consensus + RaftNode</li>
                            <li>MessageStorage</li>
                            <li>Failover + TimeSync</li>
                        </ul>
                    </div>
                    <div class="node-box">
                        <strong>Node 2</strong><br>
                        <span class="diagram-small">TCP 5002 / HTTP 5102 / Raft RPC 6002</span>
                        <ul>
                            <li>ClusterServer</li>
                            <li>Consensus + RaftNode</li>
                            <li>MessageStorage</li>
                            <li>Failover + TimeSync</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="diagram-panel">
            <h3>2. Message write path</h3>
            <p>The UI discovers the leader from <code>/status</code>, opens a socket connection to the leader TCP port, then sends the same JSON message shape used by the terminal client.</p>
            <div class="flow-track">
                <div class="flow-step">
                    <div class="step-num">1</div>
                    <h4>User sends chat</h4>
                    <p>Streamlit collects username and message text, then connects to the current leader through <code>SocketChatClient</code>.</p>
                </div>
                <div class="flow-step">
                    <div class="step-num">2</div>
                    <h4>Leader receives JSON</h4>
                    <p><code>ClusterServer.handle_client</code> parses login, chat, and logout messages from the TCP socket.</p>
                </div>
                <div class="flow-step">
                    <div class="step-num">3</div>
                    <h4>Message gets timestamp</h4>
                    <p><code>TimeSync.get_synced_time()</code> supplies an NTP-adjusted timestamp, falling back to local time if NTP is unavailable.</p>
                </div>
                <div class="flow-step">
                    <div class="step-num">4</div>
                    <h4>Raft replicates command</h4>
                    <p><code>MessageStorage.store_message()</code> creates a <code>store_message</code> command and asks the leader Raft node to replicate it.</p>
                </div>
                <div class="flow-step">
                    <div class="step-num">5</div>
                    <h4>Storage applies commit</h4>
                    <p>After majority commit, each node applies the log command through the storage state-machine callback.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="diagram-panel">
            <h3>3. Raft consensus implementation</h3>
            <p>The project implements Raft manually in <code>src/consensus/raft_node.py</code>. The <code>Consensus</code> wrapper keeps the rest of the system isolated from Raft internals.</p>
            <div class="state-grid">
                <div class="state-card">
                    <h4>Follower</h4>
                    <p>Default state. It waits for leader heartbeats. If no heartbeat arrives before the randomized timeout, it starts an election.</p>
                </div>
                <div class="state-card">
                    <h4>Candidate</h4>
                    <p>Increments term, votes for itself, sends <code>RequestVote</code> RPCs, and becomes leader if it wins quorum.</p>
                </div>
                <div class="state-card">
                    <h4>Leader</h4>
                    <p>Sends heartbeats every 50 ms, appends client commands to its log, and replicates entries through <code>AppendEntries</code>.</p>
                </div>
            </div>
            <div class="flow-track">
                <div class="flow-step">
                    <div class="step-num">A</div>
                    <h4>Election timeout</h4>
                    <p>Each follower has a random 150-300 ms timeout to reduce simultaneous elections.</p>
                </div>
                <div class="flow-step">
                    <div class="step-num">B</div>
                    <h4>Request votes</h4>
                    <p>The candidate sends term, candidate ID, and log position to the other Raft RPC ports.</p>
                </div>
                <div class="flow-step">
                    <div class="step-num">C</div>
                    <h4>Win quorum</h4>
                    <p>In a three-node cluster, two votes are enough to form a majority and elect one leader.</p>
                </div>
                <div class="flow-step">
                    <div class="step-num">D</div>
                    <h4>Send heartbeats</h4>
                    <p>The leader continuously sends empty or populated <code>AppendEntries</code> calls to keep followers aligned.</p>
                </div>
                <div class="flow-step">
                    <div class="step-num">E</div>
                    <h4>Commit entries</h4>
                    <p>The leader advances <code>commit_index</code> after a majority match the log entry for the current term.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="diagram-panel">
            <h3>4. Fault tolerance and failover timeline</h3>
            <p>Failover is handled by two cooperating mechanisms: Raft detects leader silence through missed heartbeats, while the Failover component performs TCP health checks and exposes healthy nodes to the HTTP status API.</p>
            <div class="timeline">
                <div class="timeline-card">
                    <strong>T0: Healthy cluster</strong>
                    <p>One leader sends heartbeats. Two followers keep their election timers reset.</p>
                </div>
                <div class="timeline-card">
                    <strong>T1: Node failure</strong>
                    <p>TCP health checks remove the failed node from <code>healthy_nodes</code>. If it was leader, heartbeats stop.</p>
                </div>
                <div class="timeline-card">
                    <strong>T2: New election</strong>
                    <p>A follower times out, becomes candidate, requests votes, and wins if a majority is still reachable.</p>
                </div>
                <div class="timeline-card">
                    <strong>T3: Service continues</strong>
                    <p>The new leader accepts writes. The UI detects the new leader through <code>/status</code> and sends future messages there.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="diagram-panel">
            <h3>5. Component responsibility matrix</h3>
            <p>Each module has a narrow role. That separation is why the UI can explain and inspect the system without modifying backend behavior.</p>
            <div class="matrix">
                <div class="head">Component</div>
                <div class="head">Responsibility</div>
                <div class="head">Important implementation details</div>
                <div class="name">ClusterServer</div>
                <div>Owns the server lifecycle and coordinates all components inside one node process.</div>
                <div>Starts TCP socket, async event loop, consensus, storage, failover, and HTTP query API.</div>
                <div class="name">RaftNode</div>
                <div>Manual consensus engine for leader election and replicated log commitment.</div>
                <div>Uses RequestVote, AppendEntries, term tracking, randomized timeouts, heartbeats, and majority commit.</div>
                <div class="name">Consensus</div>
                <div>Small wrapper around RaftNode for the rest of the project.</div>
                <div>Tracks cached leader and exposes cluster size, quorum size, term, and state.</div>
                <div class="name">MessageStorage</div>
                <div>State machine that stores committed message JSON by message ID.</div>
                <div>Uses a local dictionary and ordered index protected by a reentrant lock. Raft calls back into storage when entries commit.</div>
                <div class="name">Failover</div>
                <div>Monitors node health and leader changes.</div>
                <div>Performs TCP checks every 3 seconds and publishes healthy nodes through status responses.</div>
                <div class="name">TimeSync</div>
                <div>Provides consistent timestamps for messages.</div>
                <div>Tries multiple NTP servers, keeps an offset, and periodically resynchronizes in the background.</div>
                <div class="name">HTTPQueryAPI</div>
                <div>Read-only observability layer for the UI and terminal demos.</div>
                <div><code>/status</code> returns leader/state/term/health. <code>/messages</code> returns that node's local stored messages.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="diagram-panel">
            <h3>6. What the demo proves</h3>
            <div class="explain-grid">
                <div class="explain-card">
                    <h3>Leader election</h3>
                    <p>The Cluster tab shows which node is leader, the current Raft term, and how leadership changes after stopping a node.</p>
                </div>
                <div class="explain-card">
                    <h3>Replication</h3>
                    <p>The Storage Inspector calls every node's <code>/messages</code> endpoint so you can compare the local state machines side by side.</p>
                </div>
                <div class="explain-card">
                    <h3>Fault tolerance</h3>
                    <p>Stopping one node leaves a majority available. A new leader can be elected and the app will send future messages to that leader.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Distributed Messaging UI", page_icon="DM", layout="wide")
    init_state()
    st.markdown(css_block(), unsafe_allow_html=True)

    controller: ProcessController = st.session_state.controller
    api: ClusterApiClient = st.session_state.api_client

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">Live Cluster Dashboard</div>
            <h1>Distributed Messaging Control Room</h1>
            <p>
                Start the cluster, send chat messages, inspect leader election, compare per-node
                message storage, and read process logs from one demo surface.
            </p>
            <div class="hero-badges">
                <span class="node-pill leader">Raft state</span>
                <span class="node-pill running">Storage sync</span>
                <span class="node-pill follower">Node telemetry</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## Demo Controls")
        st.caption("These controls launch or manage the existing Python node processes.")

        st.session_state.selected_node = st.radio(
            "Target node",
            options=[0, 1, 2],
            index=int(st.session_state.selected_node),
            format_func=lambda node_id: f"Node {node_id} (port {5000 + node_id})",
        )

        control_cols = st.columns(2)
        with control_cols[0]:
            if st.button("Start", use_container_width=True):
                with st.spinner("Starting node..."):
                    controller.start_node(int(st.session_state.selected_node))
                st.session_state.last_action = f"Started node {st.session_state.selected_node}."
                st.session_state.status_message = "Start requested. Refreshing cluster state."
                st.rerun()
        with control_cols[1]:
            if st.button("Stop", use_container_width=True):
                with st.spinner("Stopping node..."):
                    stopped = controller.stop_node(int(st.session_state.selected_node))
                st.session_state.last_action = f"Stopped node {st.session_state.selected_node}."
                st.session_state.status_message = "Stop requested." if stopped else "Stop requested, but the node may already be external or stopped."
                st.session_state.chat_client.close()
                st.rerun()

        if st.button("Restart selected node", use_container_width=True):
            with st.spinner("Restarting node..."):
                controller.restart_node(int(st.session_state.selected_node))
            st.session_state.last_action = f"Restarted node {st.session_state.selected_node}."
            st.session_state.status_message = "Restart requested. Give Raft a moment to settle."
            st.session_state.chat_client.close()
            st.rerun()

        st.divider()
        if st.button("Start full cluster", use_container_width=True):
            with st.spinner("Starting cluster..."):
                for node in NODE_DEFS:
                    controller.start_node(node["node_id"])
            st.session_state.last_action = "Started all cluster nodes."
            st.session_state.status_message = "Cluster start requested. Wait a moment for leader election."
            st.rerun()

        if st.button("Stop full cluster", use_container_width=True):
            with st.spinner("Stopping cluster..."):
                stopped_count = 0
                for node in NODE_DEFS:
                    if controller.stop_node(node["node_id"]):
                        stopped_count += 1
            st.session_state.chat_client.close()
            st.session_state.last_action = "Stopped all cluster nodes."
            st.session_state.status_message = f"Stop requested for full cluster ({stopped_count}/3 reported stopped)."
            st.rerun()

        st.divider()
        st.text_input("Username", key="username")
        st.text_input("Chat message", key="message_text")

        if st.button("Send message", type="primary", use_container_width=True):
            message_text = st.session_state.message_text.strip()
            if not message_text:
                st.session_state.status_message = "Message text is required."
            else:
                with st.spinner("Sending through current leader..."):
                    statuses = get_statuses(api)
                    ok, detail, leader = send_message_via_leader(statuses, message_text)
                st.session_state.status_message = detail
                if ok and leader is not None:
                    st.session_state.last_action = f"Sent message via leader {leader.node_id}."
            st.rerun()

        if st.button("Disconnect chat client", use_container_width=True):
            result = st.session_state.chat_client.logout()
            st.session_state.status_message = result.detail
            st.session_state.last_action = "Disconnected chat client."
            st.rerun()

        st.divider()
        if st.button("Refresh dashboard", use_container_width=True):
            st.rerun()
        st.checkbox("Auto-refresh dashboard", key="auto_refresh")
        if st.session_state.auto_refresh:
            st.caption("Auto-refreshing every 4 seconds.")
            st.markdown("<meta http-equiv='refresh' content='4'>", unsafe_allow_html=True)
        st.caption(st.session_state.status_message)
        if st.session_state.last_action:
            st.caption(f"Last action: {st.session_state.last_action}")

    statuses = get_statuses(api)
    status_by_port = {status.http_port: status for status in statuses}
    leader = get_leader_node(statuses)
    storage_snapshots = api.get_storage_snapshots(http_ports())
    leader_http_port = int(leader.node_id.split(":")[-1]) + 100 if leader else None
    leader_snapshot = storage_snapshots.get(leader_http_port) if leader_http_port else None
    fallback_snapshot = next((snapshot for snapshot in storage_snapshots.values() if snapshot.reachable), None)
    feed_snapshot = leader_snapshot if leader_snapshot and leader_snapshot.reachable else fallback_snapshot
    messages = feed_snapshot.messages if feed_snapshot else []

    reachable_count = sum(1 for status in status_by_port.values() if status is not None)
    managed_count = sum(1 for node in NODE_DEFS if controller.is_running(node["node_id"]))
    leader_label = leader.node_id if leader else "No leader yet"
    term_label = str(leader.term) if leader else "-"
    consistency_title, consistency_detail, _ = storage_consistency_summary(storage_snapshots)

    top_cols = st.columns(4)
    with top_cols[0]:
        render_metric("Cluster Nodes", "3", f"{reachable_count} HTTP reachable / {managed_count} UI-managed")
    with top_cols[1]:
        render_metric("Leader", leader_label, "Election tracked from /status")
    with top_cols[2]:
        render_metric("Term", term_label, "Current Raft election term")
    with top_cols[3]:
        render_metric("Storage", consistency_title, consistency_detail)

    st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)

    tab_cluster, tab_chat, tab_storage, tab_explainer, tab_logs = st.tabs(
        ["Cluster", "Chat & Messages", "Storage Inspector", "System Explained", "Logs"]
    )

    with tab_cluster:
        node_cols = st.columns(3)
        for idx, node in enumerate(NODE_DEFS):
            with node_cols[idx]:
                render_node_card(
                    node,
                    status_by_port.get(node["http_port"]),
                    controller.is_running(node["node_id"]),
                    storage_snapshots[node["http_port"]],
                )

        with st.expander("How this UI maps to the backend"):
            st.write(
                """
                - Start, stop, and restart controls launch the existing `src/server_cluster.py` processes.
                - Message sending uses the same socket protocol as the terminal client.
                - Status and storage views read `http://127.0.0.1:<port+100>/status` and `/messages`.
                - Raft, failover, timestamping, and storage code are not changed by this UI.
                """
            )

    with tab_chat:
        left, right = st.columns([1.15, 0.85], gap="large")
        with left:
            st.markdown("<div class='panel'><div class='panel-title'>Leader Message Feed</div></div>", unsafe_allow_html=True)
            source = f"HTTP {feed_snapshot.http_port}" if feed_snapshot else "no reachable node"
            st.markdown(
                f"<div class='footer-note'>Showing messages from {escape(source)}. Use Storage Inspector to compare every node.</div>",
                unsafe_allow_html=True,
            )
            render_message_feed(messages)
        with right:
            st.markdown("<div class='panel'><div class='panel-title'>Send Path</div></div>", unsafe_allow_html=True)
            st.write(
                {
                    "username": st.session_state.username,
                    "current_client_server": st.session_state.chat_client.server,
                    "leader": leader_label,
                    "message_count_in_feed": len(messages),
                }
            )

    with tab_storage:
        render_storage_inspector(storage_snapshots)

    with tab_explainer:
        render_system_explainer()

    with tab_logs:
        selected = int(st.session_state.selected_node)
        st.markdown("<div class='panel'><div class='panel-title'>Node Console</div></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='footer-note'>Tail of node {selected} stdout/stderr log for nodes launched from this UI.</div>",
            unsafe_allow_html=True,
        )
        render_log_tail(controller, selected)


if __name__ == "__main__":
    main()

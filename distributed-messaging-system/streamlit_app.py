from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Iterable

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.api_client import ClusterApiClient, MessageRecord, NodeStatus
from ui.process_controller import ProcessController
from ui.socket_client import SocketChatClient

NODE_DEFS = [
    {"node_id": 0, "port": 5000, "http_port": 5100},
    {"node_id": 1, "port": 5001, "http_port": 5101},
    {"node_id": 2, "port": 5002, "http_port": 5102},
]


def init_state() -> None:
    st.session_state.setdefault("controller", ProcessController(PROJECT_ROOT))
    st.session_state.setdefault("api_client", ClusterApiClient())
    st.session_state.setdefault("chat_client", SocketChatClient())
    st.session_state.setdefault("selected_node", 0)
    st.session_state.setdefault("status_message", "Ready")
    st.session_state.setdefault("last_action", "")
    st.session_state.setdefault("username", "Alice")
    st.session_state.setdefault("message_text", "Hello distributed world!")
    st.session_state.setdefault("auto_scroll", True)


def css_block() -> str:
    return """
    <style>
        :root {
            --bg: #0b1220;
            --panel: rgba(16, 24, 40, 0.84);
            --panel-2: rgba(17, 30, 49, 0.95);
            --line: rgba(148, 163, 184, 0.20);
            --text: #e5eef8;
            --muted: #93a4bd;
            --accent: #4fd1c5;
            --accent-2: #7c3aed;
            --danger: #f87171;
            --warning: #fbbf24;
            --success: #22c55e;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(79, 209, 197, 0.14), transparent 24%),
                radial-gradient(circle at top right, rgba(124, 58, 237, 0.18), transparent 28%),
                linear-gradient(180deg, #09101d 0%, #0f172a 48%, #111827 100%);
            color: var(--text);
        }
        .hero {
            padding: 1.25rem 1.4rem;
            border: 1px solid var(--line);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(8, 15, 29, 0.78));
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.28);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.4rem;
            letter-spacing: -0.03em;
        }
        .hero p {
            margin: 0.55rem 0 0;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.5;
            max-width: 920px;
        }
        .metric-card {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.92));
            border: 1px solid var(--line);
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.18);
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.35rem;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--text);
            line-height: 1.1;
        }
        .metric-subtext {
            color: var(--muted);
            font-size: 0.86rem;
            margin-top: 0.3rem;
        }
        .panel {
            padding: 1rem 1.1rem;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: var(--panel);
            box-shadow: 0 18px 38px rgba(0, 0, 0, 0.18);
        }
        .panel-title {
            margin: 0 0 0.6rem;
            font-size: 1.1rem;
            font-weight: 700;
        }
        .node-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.28rem 0.72rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            border: 1px solid transparent;
        }
        .node-pill.running { background: rgba(34, 197, 94, 0.14); color: #bbf7d0; border-color: rgba(34, 197, 94, 0.24); }
        .node-pill.stopped { background: rgba(248, 113, 113, 0.12); color: #fecaca; border-color: rgba(248, 113, 113, 0.22); }
        .node-pill.leader { background: rgba(79, 209, 197, 0.16); color: #a7f3d0; border-color: rgba(79, 209, 197, 0.26); }
        .node-pill.follower { background: rgba(124, 58, 237, 0.16); color: #ddd6fe; border-color: rgba(124, 58, 237, 0.26); }
        .streamlit-expanderHeader {
            font-weight: 700;
        }
        div[data-testid="stMetric"] {
            background: transparent;
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.35rem 0.75rem;
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.12);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(6, 11, 20, 0.96), rgba(10, 15, 24, 0.92));
            border-right: 1px solid var(--line);
        }
        .tiny-label {
            color: var(--muted);
            font-size: 0.84rem;
        }
        .msg-row {
            padding: 0.8rem 0.9rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: rgba(17, 24, 39, 0.8);
            margin-bottom: 0.55rem;
        }
        .msg-header {
            display: flex;
            justify-content: space-between;
            gap: 0.6rem;
            font-size: 0.82rem;
            color: var(--muted);
            margin-bottom: 0.35rem;
        }
        .msg-content {
            font-size: 0.98rem;
            color: var(--text);
            white-space: pre-wrap;
            line-height: 1.45;
        }
        .footer-note {
            color: var(--muted);
            font-size: 0.82rem;
            margin-top: 0.5rem;
        }
    </style>
    """


def human_time(value: float) -> str:
    try:
        return datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "Unknown time"


def status_class(status: NodeStatus | None, running: bool) -> str:
    if not running:
        return "stopped"
    if status is None:
        return "running"
    if status.state.upper() == "LEADER":
        return "leader"
    return "follower"


def render_metric(label: str, value: str, subtext: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-subtext">{subtext}</div>' if subtext else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_node_card(node_def: dict[str, int], status: NodeStatus | None, running: bool) -> None:
    pill_class = status_class(status, running)
    pill_text = "Stopped" if not running else (status.state.title() if status else "Running")
    leader_text = status.leader if status and status.leader else "-"
    healthy_count = len(status.healthy_nodes) if status else 0
    st.markdown(
        f"""
        <div class="panel">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
                <div>
                    <div class="panel-title">Node {node_def['node_id']}</div>
                    <div class="tiny-label">TCP {node_def['port']} · HTTP {node_def['http_port']}</div>
                </div>
                <span class="node-pill {pill_class}">{pill_text}</span>
            </div>
            <div style="margin-top:0.9rem; display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:0.7rem;">
                <div>
                    <div class="tiny-label">Term</div>
                    <div style="font-size:1.15rem; font-weight:700;">{status.term if status else '-'}</div>
                </div>
                <div>
                    <div class="tiny-label">Leader</div>
                    <div style="font-size:1.02rem; font-weight:700; word-break:break-word;">{leader_text}</div>
                </div>
                <div>
                    <div class="tiny-label">Healthy peers</div>
                    <div style="font-size:1.15rem; font-weight:700;">{healthy_count}</div>
                </div>
                <div>
                    <div class="tiny-label">Node ID</div>
                    <div style="font-size:1.15rem; font-weight:700;">{node_def['node_id']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_statuses(controller: ProcessController, api: ClusterApiClient) -> list[NodeStatus]:
    statuses: list[NodeStatus] = []
    for node in NODE_DEFS:
        if controller.is_running(node["node_id"]):
            status = api.get_status(node["http_port"])
            if status is not None:
                statuses.append(status)
    return statuses


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
        return "Username is required."

    leader_port = int(leader.node_id.split(":")[-1])
    current_server = st.session_state.chat_client.server
    if current_server is None or current_server[1] != leader_port or st.session_state.chat_client.username != username:
        result = st.session_state.chat_client.connect("127.0.0.1", leader_port, username)
        return result.detail if not result.ok else result.detail

    return f"Connected to leader on port {leader_port}."


def render_message_feed(messages: list[MessageRecord]) -> None:
    if not messages:
        st.info("No messages available yet. Send one from the chat panel.")
        return

    for message in messages[-100:]:
        st.markdown(
            f"""
            <div class="msg-row">
                <div class="msg-header">
                    <span><strong>{message.sender or 'SYSTEM'}</strong> · {message.message_id}</span>
                    <span>{human_time(message.timestamp)}</span>
                </div>
                <div class="msg-content">{message.content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_log_tail(controller: ProcessController, node_id: int) -> None:
    log_tail = controller.get_log_tail(node_id)
    if not log_tail:
        st.caption("No log output captured yet.")
        return
    st.code(log_tail, language="text")


def main() -> None:
    st.set_page_config(page_title="Distributed Messaging UI", page_icon="💬", layout="wide")
    init_state()
    st.markdown(css_block(), unsafe_allow_html=True)

    controller: ProcessController = st.session_state.controller
    api: ClusterApiClient = st.session_state.api_client

    st.markdown(
        """
        <div class="hero">
            <h1>Distributed Messaging Control Room</h1>
            <p>
                A polished UI for starting the cluster, sending messages, watching leader election,
                and reviewing timestamped logs without changing the Raft, storage, or failover logic.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## Demo Controls")
        st.caption("Everything below launches or controls the existing Python processes.")

        st.session_state.selected_node = st.radio(
            "Target node",
            options=[0, 1, 2],
            index=int(st.session_state.selected_node),
            format_func=lambda node_id: f"Node {node_id} (port {5000 + node_id})",
        )

        if st.button("Start selected node", use_container_width=True):
            controller.start_node(int(st.session_state.selected_node))
            st.session_state.last_action = f"Started node {st.session_state.selected_node}."
            st.rerun()

        if st.button("Restart selected node", use_container_width=True):
            controller.restart_node(int(st.session_state.selected_node))
            st.session_state.last_action = f"Restarted node {st.session_state.selected_node}."
            st.rerun()

        if st.button("Stop selected node", use_container_width=True):
            controller.stop_node(int(st.session_state.selected_node))
            st.session_state.last_action = f"Stopped node {st.session_state.selected_node}."
            st.rerun()

        st.divider()
        if st.button("Start full cluster", use_container_width=True):
            for node in NODE_DEFS:
                controller.start_node(node["node_id"])
            st.session_state.last_action = "Started all cluster nodes."
            st.rerun()

        if st.button("Stop full cluster", use_container_width=True):
            for node in NODE_DEFS:
                controller.stop_node(node["node_id"])
            st.session_state.chat_client.close()
            st.session_state.last_action = "Stopped all cluster nodes."
            st.rerun()

        st.divider()
        st.text_input("Username", key="username")
        st.text_input("Chat message", key="message_text")

        if st.button("Send message", type="primary", use_container_width=True):
            statuses = get_statuses(controller, api)
            connect_message = ensure_connection(statuses)
            leader = get_leader_node(statuses)
            if leader is None:
                st.session_state.status_message = connect_message
            else:
                send_result = st.session_state.chat_client.send_chat(st.session_state.message_text.strip())
                st.session_state.status_message = send_result.detail if send_result.ok else send_result.detail
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
        st.caption(st.session_state.status_message)
        if st.session_state.last_action:
            st.caption(f"Last action: {st.session_state.last_action}")

    statuses = get_statuses(controller, api)
    leader = get_leader_node(statuses)
    messages = api.get_messages(int(leader.node_id.split(":")[-1]) + 100 if leader else 5100) if statuses else []

    running_count = sum(1 for node in NODE_DEFS if controller.is_running(node["node_id"]))
    leader_label = leader.node_id if leader else "No leader yet"
    term_label = str(leader.term) if leader else "-"

    top_cols = st.columns(4)
    with top_cols[0]:
        render_metric("Cluster nodes", "3", f"{running_count} running")
    with top_cols[1]:
        render_metric("Leader", leader_label, "Election tracked live from /status")
    with top_cols[2]:
        render_metric("Term", term_label, "Raft election term")
    with top_cols[3]:
        render_metric("Messages", str(len(messages)), "Read from /messages")

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    node_cols = st.columns(3)
    for idx, node in enumerate(NODE_DEFS):
        status = next((item for item in statuses if item.http_port == node["http_port"]), None)
        with node_cols[idx]:
            render_node_card(node, status, controller.is_running(node["node_id"]))

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.markdown("<div class='panel'><div class='panel-title'>Message Log</div></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='footer-note'>This view is powered by the existing HTTP API and shows replicated messages with timestamps.</div>",
            unsafe_allow_html=True,
        )
        render_message_feed(messages)

    with right:
        st.markdown("<div class='panel'><div class='panel-title'>Node Console</div></div>", unsafe_allow_html=True)
        selected = int(st.session_state.selected_node)
        st.caption(f"Tail of node {selected} stdout/stderr log")
        render_log_tail(controller, selected)
        st.markdown("<div class='footer-note'>Log output comes from the existing server process; no backend logic is altered.</div>", unsafe_allow_html=True)

    with st.expander("How this UI maps to the backend"):
        st.write(
            """
            - Start/stop/restart buttons launch the existing `src/server_cluster.py` processes.
            - Message sending uses the same socket protocol as the terminal client.
            - Status and replicated message history come from `http://127.0.0.1:<port+100>/status` and `/messages`.
            - Raft, failover, and storage remain unchanged.
            """
        )


if __name__ == "__main__":
    main()

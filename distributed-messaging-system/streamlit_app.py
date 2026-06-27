from __future__ import annotations

from datetime import datetime
from html import escape
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

from ui.api_client import ClusterApiClient, MessageRecord, NodeStatus, StorageSnapshot
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


def css_block() -> str:
    return """
    <style>
        :root {
            --bg: #f6f7fb;
            --panel: #ffffff;
            --panel-soft: #f8fafc;
            --line: #d9e0ea;
            --text: #111827;
            --muted: #667085;
            --accent: #0f766e;
            --accent-soft: #ccfbf1;
            --danger: #dc2626;
            --danger-soft: #fee2e2;
            --warning: #b45309;
            --warning-soft: #fef3c7;
            --success: #15803d;
            --success-soft: #dcfce7;
        }
        .stApp {
            background: var(--bg);
            color: var(--text);
        }
        .block-container {
            padding-top: 1.4rem;
        }
        .hero {
            padding: 1.05rem 1.2rem;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            letter-spacing: 0;
            color: var(--text);
        }
        .hero p {
            margin: 0.45rem 0 0;
            color: var(--muted);
            font-size: 0.98rem;
            line-height: 1.5;
            max-width: 980px;
        }
        .metric-card {
            min-height: 104px;
            padding: 0.9rem 1rem;
            border-radius: 8px;
            background: var(--panel);
            border: 1px solid var(--line);
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }
        .metric-value {
            font-size: 1.45rem;
            font-weight: 750;
            color: var(--text);
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
            padding: 0.95rem 1rem;
            border-radius: 8px;
            border: 1px solid var(--line);
            background: var(--panel);
        }
        .panel-title {
            margin: 0 0 0.55rem;
            font-size: 1rem;
            font-weight: 750;
            color: var(--text);
        }
        .node-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.24rem 0.62rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 750;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .node-pill.running { background: var(--success-soft); color: var(--success); border-color: #bbf7d0; }
        .node-pill.stopped { background: var(--danger-soft); color: var(--danger); border-color: #fecaca; }
        .node-pill.leader { background: var(--accent-soft); color: var(--accent); border-color: #99f6e4; }
        .node-pill.follower { background: #eef2ff; color: #3730a3; border-color: #c7d2fe; }
        .node-pill.warning { background: var(--warning-soft); color: var(--warning); border-color: #fde68a; }
        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }
        .tiny-label {
            color: var(--muted);
            font-size: 0.82rem;
        }
        .msg-row {
            padding: 0.75rem 0.85rem;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel);
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
            padding: 0.85rem 1rem;
            border-radius: 8px;
            border: 1px solid var(--line);
            background: var(--panel-soft);
            margin-bottom: 0.9rem;
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
    statuses: list[NodeStatus] = []
    for node in NODE_DEFS:
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
        return result.detail

    return f"Connected to leader on port {leader_port}."


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


def main() -> None:
    st.set_page_config(page_title="Distributed Messaging UI", page_icon="DM", layout="wide")
    init_state()
    st.markdown(css_block(), unsafe_allow_html=True)

    controller: ProcessController = st.session_state.controller
    api: ClusterApiClient = st.session_state.api_client

    st.markdown(
        """
        <div class="hero">
            <h1>Distributed Messaging Control Room</h1>
            <p>
                Start the cluster, send chat messages, inspect leader election, compare per-node
                message storage, and read process logs from one demo surface.
            </p>
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
                controller.start_node(int(st.session_state.selected_node))
                st.session_state.last_action = f"Started node {st.session_state.selected_node}."
                st.rerun()
        with control_cols[1]:
            if st.button("Stop", use_container_width=True):
                controller.stop_node(int(st.session_state.selected_node))
                st.session_state.last_action = f"Stopped node {st.session_state.selected_node}."
                st.rerun()

        if st.button("Restart selected node", use_container_width=True):
            controller.restart_node(int(st.session_state.selected_node))
            st.session_state.last_action = f"Restarted node {st.session_state.selected_node}."
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
            statuses = get_statuses(api)
            connect_message = ensure_connection(statuses)
            leader = get_leader_node(statuses)
            message_text = st.session_state.message_text.strip()
            if leader is None:
                st.session_state.status_message = connect_message
            elif not message_text:
                st.session_state.status_message = "Message text is required."
            else:
                send_result = st.session_state.chat_client.send_chat(message_text)
                st.session_state.status_message = send_result.detail
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

    tab_cluster, tab_chat, tab_storage, tab_logs = st.tabs(
        ["Cluster", "Chat & Messages", "Storage Inspector", "Logs"]
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

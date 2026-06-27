# Distributed-Messaging-System
a fault tolerant distributed messaging system with replication, leader election and failover mechanism implemented with manual raft algorithm using python.

## Streamlit Demo UI

This project now includes a Streamlit-based control room for the full demonstration workflow.

### Run it

From the project root:

```powershell
pip install -r distributed-messaging-system/requirements.txt
streamlit run distributed-messaging-system/streamlit_app.py
```

### What it covers

- Start, stop, and restart cluster nodes from the UI.
- Send chat messages through the same socket protocol as the terminal client.
- View leader election, node health, term number, and healthy peers.
- Inspect replicated message history with timestamps.
- Read live node logs from the dashboard.

The Raft, failover, storage, and timestamp logic are unchanged.

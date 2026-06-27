# 🎬 LIVE DEMONSTRATION WALKTHROUGH
## Follow These Steps Exactly - I'll Guide You!

**Time:** 15-20 minutes  
**Current Status:** ✅ You have servers running!

---

## 📍 WHERE YOU ARE NOW

Based on your terminals, you have:
- ✅ **Terminal 1** - Tests completed
- ✅ **Terminal 2** - Server running (probably node 0 or 1)
- ✅ **Terminal 3** - Server running (probably node 1 or 2)
- ✅ **Terminal 4** - Client started but maybe not active

---

## 🚀 LET'S DO THE DEMO - STEP BY STEP

### STEP 1: Verify Your Servers are Running

**In any PowerShell terminal, run:**
```powershell
netstat -an | findstr "5000 5001 5002"
```

**Expected:** You should see LISTENING on ports 5000, 5001, 5002

**If NOT all 3 running:**
- Open 3 separate terminals
- In Terminal A: `python src/server_cluster.py 0`
- In Terminal B: `python src/server_cluster.py 1`
- In Terminal C: `python src/server_cluster.py 2`
- Wait 10 seconds for leader election

**✅ CHECKPOINT:** All 3 servers running? → Continue to STEP 2

---

### STEP 2: Check Which is the Leader

**Look at your server terminals** and find which one shows:
```
[RAFT] Node 127.0.0.1:5000 became LEADER
```
or
```
Leader changed to: 127.0.0.1:5000
```

**Write down the leader port:** _________ (e.g., 5000, 5001, or 5002)

**✅ CHECKPOINT:** You know the leader port? → Continue to STEP 3

---

### STEP 3: Start Interactive Client

**Open a NEW terminal (or use Terminal 5):**

```powershell
cd C:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system
.\venv\Scripts\Activate.ps1
python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002
```

**Expected:**
```
Connected to server 127.0.0.1:5000
Enter your username: _
```

**Type:** `Alice` and press Enter

**Expected:**
```
Welcome Alice! Connected to server 127.0.0.1:5000
Type your messages (Ctrl+C to exit)

> _
```

**✅ CHECKPOINT:** Client connected and waiting for input? → Continue to STEP 4

---

### STEP 4: Send Your First Message

**In the client terminal, type:**
```
Hello from distributed system!
```
**Press Enter**

**👀 WATCH YOUR SERVER TERMINALS!**

**Expected on LEADER terminal:**
```
Received message from Alice: "Hello from distributed system!"
Replicating to follower 127.0.0.1:5001... ✓
Replicating to follower 127.0.0.1:5002... ✓
Message committed
```

**Expected on FOLLOWER terminals:**
```
Received replicated message: msg_XXXXXXXXX_001
Stored message from Alice
```

**✅ CHECKPOINT:** You see replication happening? → Continue to STEP 5

---

### STEP 5: Send More Messages

**In the client terminal, type these messages (press Enter after each):**

```
Testing message replication across all nodes
```

```
Raft consensus working perfectly!
```

```
This is amazing! Zero data loss guaranteed!
```

**👀 WATCH:** Each message replicates to all nodes in real-time!

**✅ CHECKPOINT:** 4 messages sent? → Continue to STEP 6

---

### STEP 6: Verify Data Consistency

**Open ANOTHER terminal (Terminal 6) or minimize client:**

```powershell
cd C:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system
.\venv\Scripts\Activate.ps1

# Query Server 0
curl http://localhost:5000/messages
```

**Wait for output, then:**

```powershell
# Query Server 1
curl http://localhost:5001/messages
```

**Wait for output, then:**

```powershell
# Query Server 2
curl http://localhost:5002/messages
```

**👀 COMPARE THE OUTPUTS:**
- All 3 servers should return THE EXACT SAME messages!
- All 4 messages present on all nodes
- Same message IDs, same content, same order

**✅ CHECKPOINT:** All servers have identical data? → Continue to STEP 7

---

### STEP 7: Check Cluster Status

**In the same terminal:**

```powershell
curl http://localhost:5000/status
```

**Expected output (JSON):**
```json
{
  "node_id": "127.0.0.1:5000",
  "state": "LEADER" or "FOLLOWER",
  "leader": "127.0.0.1:5000",
  "cluster_size": 3,
  "healthy_nodes": [
    "127.0.0.1:5000",
    "127.0.0.1:5001",
    "127.0.0.1:5002"
  ],
  "message_count": 4,
  "term": <number>
}
```

**👀 KEY POINTS:**
- `healthy_nodes`: All 3 should be listed
- `leader`: Shows current leader
- `message_count`: Should be 4
- `term`: Current Raft term (probably 1 or higher)

**✅ CHECKPOINT:** Status looks good? → Continue to STEP 8

---

### STEP 8: THE BIG TEST - Kill the Leader! 💥

**🎯 This is the most impressive part of your demo!**

**Identify the LEADER terminal** (the one showing "LEADER" in status)

**Go to that terminal and:**
```
Press: Ctrl+C
```

**Expected on Leader terminal:**
```
^C
Shutting down...
Server stopped
```

**👀 IMMEDIATELY WATCH THE OTHER 2 TERMINALS!**

**Within 3-5 seconds, you'll see:**

**On one follower (new leader):**
```
WARN: No heartbeat from leader
Starting election for term 2
Became CANDIDATE
Received vote from 127.0.0.1:5002
✓ Elected as LEADER for term 2
Starting heartbeat broadcasts
```

**On other follower:**
```
WARN: No heartbeat from leader
Received RequestVote from 127.0.0.1:5001
Voting for 127.0.0.1:5001 in term 2
New leader elected: 127.0.0.1:5001
```

**🎉 AUTOMATIC RE-ELECTION COMPLETE!**

**Note the NEW leader port:** _________ (probably 5001 or 5002)

**✅ CHECKPOINT:** New leader elected? → Continue to STEP 9

---

### STEP 9: Send Message to New Leader

**Go back to your CLIENT terminal** (should still be running)

**Type:**
```
System recovered after failover!
```
**Press Enter**

**Expected:**
- Message sends successfully
- New leader replicates to remaining follower
- System working normally!

**✅ CHECKPOINT:** Message sent to new leader? → Continue to STEP 10

---

### STEP 10: Verify Zero Data Loss

**In Terminal 6 (curl terminal):**

```powershell
# Query the NEW leader (replace 5001 with your new leader port)
curl http://localhost:5001/messages
```

**👀 COUNT THE MESSAGES:**
- Should see 5 messages total
- 4 original messages from Alice
- 1 new message after failover
- ALL messages preserved!

**✅ ZERO DATA LOSS CONFIRMED! 🎉**

**✅ CHECKPOINT:** All 5 messages present? → Continue to STEP 11

---

### STEP 11: Check Cluster Status After Failover

```powershell
curl http://localhost:5001/status
```

**Expected:**
```json
{
  "leader": "127.0.0.1:5001",  ← NEW leader
  "term": 2,                    ← Term increased!
  "cluster_size": 3,
  "healthy_nodes": [            ← Only 2 nodes now
    "127.0.0.1:5001",
    "127.0.0.1:5002"
  ],
  "message_count": 5
}
```

**👀 KEY CHANGES:**
- `leader`: Changed to new node
- `term`: Increased from 1 to 2
- `healthy_nodes`: Only 2 (failed node missing)
- `message_count`: Still 5 (no data loss!)

**✅ CHECKPOINT:** Status shows 2 healthy nodes? → Continue to STEP 12

---

### STEP 12: Restart the Failed Node

**Go to the terminal where you pressed Ctrl+C**

```powershell
# Restart the failed node (use same command as before)
# If it was node 0: python src/server_cluster.py 0
# If it was node 1: python src/server_cluster.py 1
# If it was node 2: python src/server_cluster.py 2

python src/server_cluster.py 0
```

**Expected output:**
```
Node initialized in FOLLOWER state
Discovered leader: 127.0.0.1:5001
Syncing with leader...
✓ Received 5 messages from leader
Node synchronized, ready to serve
```

**👀 WATCH:** Node automatically:
- Starts as FOLLOWER
- Finds current leader
- Syncs missing data
- Becomes healthy!

**Wait 5 seconds for sync to complete**

**✅ CHECKPOINT:** Node restarted and synced? → Continue to STEP 13

---

### STEP 13: Verify Full Cluster Restored

```powershell
curl http://localhost:5001/status
```

**Expected:**
```json
{
  "healthy_nodes": [
    "127.0.0.1:5000",  ← Recovered node back!
    "127.0.0.1:5001",
    "127.0.0.1:5002"
  ],
  "cluster_size": 3,
  "message_count": 5
}
```

**✅ ALL 3 NODES HEALTHY AGAIN! 🎉**

---

### STEP 14: Verify Recovered Node Has All Data

```powershell
# Query the recovered node
curl http://localhost:5000/messages
```

**Expected:**
- All 5 messages present
- Synced from leader during recovery
- Perfect consistency!

**✅ CHECKPOINT:** Recovered node has all 5 messages? → Demo Complete! 🎉

---

## 🏆 WHAT YOU JUST DEMONSTRATED

### ✅ Unit Testing
- 19/19 tests passing
- All components verified independently

### ✅ Distributed Consensus
- Automatic leader election
- Raft algorithm working correctly
- No manual configuration needed

### ✅ Message Replication
- Real-time replication to all nodes
- Strong consistency maintained
- All nodes have identical data

### ✅ Fault Tolerance
- Leader failure detected automatically
- New leader elected in 3-5 seconds
- System continues operating

### ✅ Zero Data Loss
- All messages preserved during failover
- No data corruption
- Perfect consistency maintained

### ✅ Automatic Recovery
- Failed node rejoins cluster
- Discovers leader automatically
- Syncs missing data
- Full cluster restored

---

## 📸 SCREENSHOTS TO TAKE

For your report, capture:

1. ✅ Test results (19/19 passing)
2. ✅ 3 servers running (show all terminals)
3. ✅ Leader election messages
4. ✅ Client sending messages
5. ✅ Replication logs on servers
6. ✅ curl outputs (all nodes same data)
7. ✅ Leader failure (Ctrl+C)
8. ✅ Re-election messages
9. ✅ New leader elected
10. ✅ Cluster status (before/after failover)
11. ✅ Node recovery
12. ✅ Final cluster status (all 3 healthy)

---

## 🎤 WHAT TO SAY DURING DEMO

**Opening:**
> "Today I'll demonstrate our distributed messaging system with automatic failover and zero data loss."

**Unit Tests:**
> "First, let's verify all components work independently. [Run tests] All 19 tests pass - 100% success."

**Starting Cluster:**
> "Now I'll start our 3-node cluster. Watch as they elect a leader automatically through Raft consensus."

**Sending Messages:**
> "Let me send some messages as a user. Watch the server terminals - you'll see real-time replication."

**Verification:**
> "Let's verify all nodes have the same data. [Run curl] See? All three nodes return identical messages."

**Failure Scenario:**
> "Now the exciting part - what happens if the leader crashes? [Press Ctrl+C] Watch the terminals..."

**Re-election:**
> "Within seconds, a new leader is elected automatically. No manual intervention needed."

**Zero Data Loss:**
> "Let's verify no data was lost. [Run curl] All messages are still here - zero data loss!"

**Recovery:**
> "Now I'll restart the failed node. [Restart] Watch as it discovers the leader and syncs automatically."

**Conclusion:**
> "As you can see, our system provides automatic failover, zero data loss, and seamless recovery - exactly what a distributed system should do."

---

## 🚦 STATUS TRACKER

Track your progress:

- [ ] STEP 1: Servers verified
- [ ] STEP 2: Leader identified
- [ ] STEP 3: Client connected
- [ ] STEP 4: First message sent
- [ ] STEP 5: Multiple messages sent
- [ ] STEP 6: Data consistency verified
- [ ] STEP 7: Cluster status checked
- [ ] STEP 8: Leader killed
- [ ] STEP 9: Message to new leader
- [ ] STEP 10: Zero data loss verified
- [ ] STEP 11: Cluster status after failover
- [ ] STEP 12: Failed node restarted
- [ ] STEP 13: Full cluster restored
- [ ] STEP 14: Recovered node verified

**When all checked: YOUR DEMO IS COMPLETE! 🎉**

---

## 💡 TROUBLESHOOTING

**If client won't connect:**
- Verify servers running: `netstat -an | findstr "5000 5001 5002"`
- Restart servers if needed

**If no leader elected:**
- Wait 10 seconds
- Restart all servers: Ctrl+C all, then restart 0, 1, 2

**If replication not showing:**
- Check you're looking at correct server terminals
- Leader shows "Replicating to..."
- Followers show "Received replicated message"

**If curl fails:**
- Check port number (5000, 5001, or 5002)
- Verify server running on that port
- Try another port

---

## 🎯 NEXT STEPS

**After completing this demo:**

1. ✅ Take all screenshots
2. ✅ Save terminal logs
3. ✅ Stop all servers (Ctrl+C)
4. ✅ Stop client (Ctrl+C)
5. ✅ Organize evidence for report
6. ✅ Practice once more before actual presentation

---

**YOU'VE GOT THIS! Your system works perfectly - just follow these steps and you'll have an amazing demo! 💪**

**Good luck! 🚀**

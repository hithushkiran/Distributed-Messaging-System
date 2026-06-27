# 🖥️ Terminal Demonstration Script
## Distributed Messaging System - Command-by-Command Guide

**Purpose:** Exact terminal commands for demonstrating your distributed messaging system  
**Time:** 15-20 minutes  
**Terminals Needed:** 5 (or use split panes)

---

## 📋 Quick Setup

### Before Demo: Clean State
```powershell
# Navigate to project
cd C:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Clean old logs
Remove-Item -Path src\logs\* -Recurse -Force -ErrorAction SilentlyContinue
New-Item -Path src\logs\0 -ItemType Directory -Force
New-Item -Path src\logs\1 -ItemType Directory -Force
New-Item -Path src\logs\2 -ItemType Directory -Force

# Clear terminal
Clear-Host
```

---

## 📖 Understanding the Demo Flow

### What You'll Demonstrate:

**1. Unit Tests (Part 1):**
- Run automated tests for all 4 components
- Show 19/19 tests passing (100% success)
- Prove each component works independently

**2. Cluster Startup (Part 2):**
- Start 3 servers (ports 5000, 5001, 5002)
- Watch automatic leader election via Raft consensus
- No manual configuration needed

**3. Send Messages (Part 3):**
- Connect interactive client to cluster
- Type messages as a user would
- Watch real-time replication across all nodes

**4. Verify Replication (Part 4):**
- Query all 3 servers using curl
- Confirm all nodes have identical data
- Show strong consistency in action

**5. Failure & Recovery (Part 5):**
- Kill the leader (Ctrl+C)
- Watch automatic re-election (3-5 seconds)
- Send new messages to new leader
- Verify zero data loss

**6. Node Recovery (Part 6):**
- Restart the failed node
- Watch it discover leader and sync data
- Verify full cluster restoration

### Key Concepts to Explain:

**Raft Consensus:**
- Algorithm for distributed agreement
- Elects one leader among nodes
- Leader handles all writes
- Followers replicate data from leader

**Leader Election:**
- Happens automatically when cluster starts
- Re-election triggers if leader fails
- Requires majority vote (2 out of 3 nodes)
- Term number increases with each election

**Message Replication:**
- Client sends message to any server
- Server redirects to leader if needed
- Leader stores message locally
- Leader replicates to all followers
- Confirms when majority have stored it

**Fault Tolerance:**
- System survives 1 node failure (in 3-node cluster)
- Automatic failover (no manual intervention)
- Zero data loss during failover
- Failed nodes can rejoin and sync

---

## 🎯 Part 1: Unit Tests Demonstration (3 minutes)

### Terminal 1: Run All Tests

```powershell
# Show all tests passing
./venv/Scripts/python.exe tests/test_all_members_simple.py
```

**Wait for output:** All 19 tests should pass with ✓ marks

**SAY:** "All 19 unit tests pass - every component is verified to work independently."

---

### Terminal 1: Show Individual Member Tests

```powershell
# Member 1: Failover tests
./venv/Scripts/python.exe tests/test_member1_individual.py
```

**Wait 1 second, then:**

```powershell
# Member 2: Storage tests
./venv/Scripts/python.exe tests/test_member2_individual.py
```

**Wait 1 second, then:**

```powershell
# Member 3: TimeSync tests
./venv/Scripts/python.exe tests/test_member3_individual.py
```

**Wait 1 second, then:**

```powershell
# Member 4: Consensus tests
./venv/Scripts/python.exe tests/test_member4_individual.py
```

**SAY:** "Each member can verify their component independently."

---

## 🚀 Part 2: Start the Cluster (3 minutes)

**⚠️ IMPORTANT:** Use `server_cluster.py` (not `server.py`) for the distributed system demo!

### Terminal 2: Start Server 0

```powershell
# Start first server (node 0 in 3-node cluster)
python src/server_cluster.py
```

**Expected:** Server starts on port 5000, shows "Starting Raft consensus", "Starting failover monitoring"  
**SAY:** "Starting Node 0 on port 5000..."

---

### Terminal 3: Start Server 1

```powershell
# Start second server (node 1 in 3-node cluster)
python src/server_cluster.py 1
```

**Expected:** Server starts on port 5001, begins discovering other nodes  
**SAY:** "Starting Node 1 on port 5001..."

---

### Terminal 4: Start Server 2

```powershell
# Start third server (node 2 in 3-node cluster)
python src/server_cluster.py 2
```

**Expected:** Server starts on port 5002, cluster forms, leader election begins!  
**SAY:** "Starting Node 2 on port 5002... Now watch for leader election."

---

### **⏱️ WAIT 5-10 SECONDS - Watch Terminals for Leader Election**

**Look for:** One terminal shows "✓ Elected as LEADER"  
**Note:** Which port is the leader (5000, 5001, or 5002)

**SAY:** "Node [X] has been elected as leader automatically through Raft consensus."

---

## 📤 Part 3: Send Messages (3 minutes)

### Terminal 5: Start Interactive Client

**Note:** The client automatically connects to any available server in the cluster

```powershell
# Start interactive client (connects to cluster)
python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002
```

**Expected Output:**
```
Connected to server 127.0.0.1:5000
Enter your username: _
```

**SAY:** "The client connects to the cluster. It will automatically find the leader."

---

### Send Messages Interactively

**Type in the client terminal:**

1. **Enter username:**
   ```
   Alice
   ```
   
2. **Send first message:**
   ```
   Hello from distributed system!
   ```
   **Press Enter**
   
   **SAY:** "Watch the server terminals - you'll see the leader receive and replicate this message."

3. **Send second message:**
   ```
   Testing message replication across all nodes
   ```
   **Press Enter**

4. **Send third message:**
   ```
   Raft consensus working perfectly!
   ```
   **Press Enter**

**Expected on Server Terminals:**
- **Leader terminal:** Shows "Received message from Alice", "Replicating to followers"
- **Follower terminals:** Show "Received replicated message"

**SAY:** "Notice how the leader replicates each message to all followers immediately. This ensures data consistency across the cluster."

---

### Keep Client Running

**DON'T close the client yet** - we'll use it to verify messages later.

**SAY:** "Let's verify that all nodes have the same messages..."

---

### 💡 What Just Happened? (Explanation for Audience)

**Client Connection:**
1. Client tries to connect to any server in cluster
2. If connected to follower, follower tells client who the leader is
3. Client redirects writes to the leader

**Message Flow:**
```
Client → Leader Server (port 5000)
           ↓
    Leader stores message
           ↓
    Leader replicates to followers
           ↓
    ┌──────────┴──────────┐
    ↓                     ↓
Follower 1            Follower 2
(port 5001)          (port 5002)
    ↓                     ↓
Store message        Store message
    ↓                     ↓
Ack to leader       Ack to leader
           ↓
    Leader confirms to client
```

**Key Points:**
- ✅ Leader handles all writes (Raft requirement)
- ✅ Synchronous replication (strong consistency)
- ✅ Majority must confirm before commit
- ✅ All nodes end up with identical data

---

## 🔍 Part 4: Verify Replication (2 minutes)

### Terminal 5: Query All Servers

```powershell
# Query server 0
curl http://localhost:5000/messages
```

**Expected:** JSON with 3 messages

**Wait 1 second, then:**

```powershell
# Query server 1
curl http://localhost:5001/messages
```

**Expected:** Same 3 messages

**Wait 1 second, then:**

```powershell
# Query server 2
curl http://localhost:5002/messages
```

**Expected:** Same 3 messages

**SAY:** "All three nodes have identical data - strong consistency maintained."

---

### Terminal 5: Check Cluster Status

```powershell
# Check cluster status (replace 5000 with leader port)
curl http://localhost:5000/status
```

**Expected:** JSON showing leader, healthy nodes, term, message count

**SAY:** "This shows our leader, all healthy nodes, and cluster state."

---

## ⚠️ Part 5: Leader Failure & Recovery (5 minutes)

### **IDENTIFY THE LEADER TERMINAL** (from Part 2)

**SAY:** "Now let's test fault tolerance. What happens if the leader crashes?"

---

### Leader Terminal: Kill the Leader

```
Press: Ctrl+C
```

**Expected:** Leader shuts down  
**SAY:** "Leader is down. Watch the remaining terminals..."

---

### **⏱️ WAIT 3-5 SECONDS - Watch Re-Election**

**Look for:**
- Follower terminals show: "WARN: No heartbeat from leader"
- One terminal shows: "Starting election for term 2"
- One terminal shows: "✓ Elected as LEADER for term 2"

**Note:** Which port is the NEW leader

**SAY:** "New leader elected automatically! The system recovered in seconds without manual intervention."

---

### Terminal 5: Send Message to New Leader

**⚠️ Replace with NEW leader port!**

```powershell
# Send message to new leader
python src/client.py 5001 "System recovered after failover!" Dave
```

**Expected:** ✓ Message sent successfully  
**SAY:** "System is operational with the new leader."

---

### Terminal 5: Verify No Data Loss

```powershell
# Query new leader
curl http://localhost:5001/messages
```

**Expected:** JSON with 4 messages (3 old + 1 new)

**SAY:** "All messages are safe - zero data loss during failover."

---

### Terminal 5: Check New Cluster Status

```powershell
# Check status
curl http://localhost:5001/status
```

**Expected:** 
- 2 healthy nodes (failed node is missing)
- New leader shown
- Term increased (was 1, now 2)

**SAY:** "Notice the term increased from 1 to 2, and we have 2 healthy nodes."

---

## 🔄 Part 6: Node Recovery (3 minutes)

### Previously Failed Terminal: Restart the Node

**Use the terminal where you pressed Ctrl+C**

```powershell
# Restart the failed node (node 0 if that was the failed one)
python src/server_cluster.py 0
# Or if node 1 failed: python src/server_cluster.py 1
# Or if node 2 failed: python src/server_cluster.py 2
```

**Expected:**
- Node starts in FOLLOWER state
- Discovers current leader
- Syncs missing data
- "✓ Received X messages from leader"

**SAY:** "The recovered node rejoins the cluster, discovers the leader, and syncs automatically."

---

### **⏱️ WAIT 3-5 SECONDS for Sync**

---

### Terminal 5: Verify Full Cluster Restored

```powershell
# Check cluster status
curl http://localhost:5001/status
```

**Expected:**
- 3 healthy nodes
- All nodes listed
- Message count: 4

**SAY:** "The cluster is fully restored with all 3 nodes healthy again."

---

### Terminal 5: Verify Recovered Node Has All Data

```powershell
# Query the recovered node
curl http://localhost:5000/messages
```

**Expected:** All 4 messages (synced from leader)

**SAY:** "The recovered node has all messages - perfect consistency."

---

## 🎬 Optional Demos (If Time Allows)

### Optional 1: Query Specific Message

```powershell
# Get specific message by ID (copy an ID from previous query)
curl http://localhost:5000/message/msg_1728234605_001
```

---

### Optional 2: Try Sending to Follower

```powershell
# Try sending to a follower (should fail)
python src/client.py 5002 "This should be rejected" Eve
```

**Expected:** Error message saying "not the leader"  
**SAY:** "Followers correctly reject write requests - only the leader accepts writes."

---

### Optional 3: Send Multiple Messages Rapidly

```powershell
python src/client.py 5001 "Message 1" User1
python src/client.py 5001 "Message 2" User2
python src/client.py 5001 "Message 3" User3
python src/client.py 5001 "Message 4" User4
python src/client.py 5001 "Message 5" User5
```

**SAY:** "Leader handles concurrent requests and maintains consistency."

---

### Optional 4: Check Message Count

```powershell
# Count messages
curl http://localhost:5001/messages | ConvertFrom-Json | Select-Object -ExpandProperty count
```

---

## 🛑 Cleanup After Demo

### All Server Terminals (2, 3, 4):

```
Press: Ctrl+C
```

Wait for clean shutdown on each.

---

### Terminal 5: Verify All Stopped

```powershell
# Check no servers running
netstat -an | findstr "5000 5001 5002"
```

**Expected:** No output (all ports free)

---

## 📊 Summary of What You Demonstrated

✅ **Unit Tests:** 19/19 tests passing  
✅ **Leader Election:** Automatic, no manual intervention  
✅ **Message Replication:** All nodes have identical data  
✅ **Strong Consistency:** Verified by querying multiple nodes  
✅ **Automatic Failover:** New leader elected in 3-5 seconds  
✅ **Zero Data Loss:** All messages preserved after failure  
✅ **Automatic Recovery:** Failed node rejoins and syncs automatically  
✅ **Full Cluster Restoration:** All 3 nodes healthy again

---

## 🎯 Command Reference Sheet

### Quick Commands for Demo

```powershell
# START DEMO
./venv/Scripts/python.exe tests/test_all_members_simple.py
python src/server_cluster.py 0    # Terminal 2 (node 0, port 5000)
python src/server_cluster.py 1    # Terminal 3 (node 1, port 5001)
python src/server_cluster.py 2    # Terminal 4 (node 2, port 5002)

# START CLIENT (interactive mode)
python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002
# Then type username and messages interactively

# VERIFY DATA
curl http://localhost:5000/messages
curl http://localhost:5001/messages
curl http://localhost:5002/messages

# CHECK STATUS
curl http://localhost:5000/status

# KILL LEADER
Ctrl+C  # On leader terminal

# RESTART NODE
python src/server_cluster.py 0    # If node 0 failed
python src/server_cluster.py 1    # If node 1 failed
python src/server_cluster.py 2    # If node 2 failed

# CLEANUP
Ctrl+C  # On all server terminals
```

---

## 🐛 Troubleshooting Quick Fixes

### **CRITICAL:** server.py vs server_cluster.py

**Problem:** No leader elected, no Raft consensus messages

**Cause:** Using `server.py` instead of `server_cluster.py`

**Explanation:**
- `server.py` = Simple standalone server (no clustering, no Raft)
- `server_cluster.py` = Full distributed system with Raft consensus

**Solution:** Always use `server_cluster.py` for demos!

```powershell
# WRONG - No leader election
python src/server.py --port 5000

# CORRECT - Full distributed system
python src/server_cluster.py 0    # or just: python src/server_cluster.py
python src/server_cluster.py 1
python src/server_cluster.py 2
```

### Port Already in Use
```powershell
netstat -ano | findstr ":5000"
taskkill /PID <PID> /F
```

### Can't Connect to Server
```powershell
# Verify server running
curl http://localhost:5000/status

# Check leader port
# Look at server terminals for "✓ Elected as LEADER"
```

### Leader Not Elected
```powershell
# Wait 10 seconds
# If still no leader, restart all servers:
# Ctrl+C on all, then restart in order: 5000, 5001, 5002
```

---

## 📝 Demo Checklist

**Before Starting:**
- [ ] 5 terminals ready (or split panes configured)
- [ ] Virtual environment activated
- [ ] Logs cleaned
- [ ] No servers running from previous demo

**During Demo:**
- [ ] Run tests first (builds confidence)
- [ ] Note which port is leader
- [ ] Wait for leader election before sending messages
- [ ] Highlight replication in server logs
- [ ] Verify consistency by querying multiple servers
- [ ] Kill leader and watch re-election
- [ ] Show zero data loss

**After Demo:**
- [ ] Stop all servers cleanly
- [ ] Save terminal logs if needed
- [ ] Take screenshots for report

---

## 🎤 Pro Tips

1. **Increase terminal font size** before demo (Right-click → Properties → Font → 16-18)
2. **Arrange terminals** side-by-side (3 servers visible + 1 client)
3. **Explain before executing** each command
4. **Point at screens** when highlighting log messages
5. **Use different colors** for each terminal if possible
6. **Practice twice** before actual demo
7. **Have this script open** on a separate screen for reference
8. **Stay calm** - if something breaks, restart from Part 2

---

## ⏱️ Timing Guide

| Section | Time | Critical? |
|---------|------|-----------|
| Unit Tests | 3 min | ✅ Yes |
| Start Cluster | 3 min | ✅ Yes |
| Send Messages | 3 min | ✅ Yes |
| Verify Replication | 2 min | ✅ Yes |
| Leader Failure | 5 min | ✅ YES! Most impressive |
| Node Recovery | 3 min | ⚠️ If time allows |
| Optional Demos | 5 min | ❌ Skip if short on time |

**Minimum viable demo:** 16 minutes (all ✅ sections)

---

**🚀 You're Ready! Follow these commands step-by-step and your demo will be perfect!**

**Remember:** 
- Note the leader port after election
- Wait for elections to complete (5-10 seconds)
- Highlight the automatic behaviors (election, replication, recovery)
- Point out the zero data loss

**Good luck! 💪**

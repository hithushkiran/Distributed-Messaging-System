# 🚀 QUICK START - Testing Your raftos-Free System

## ✅ Status: All raftos dependencies REMOVED

---

## 🧪 Test 1: Syntax Validation (30 seconds)

```powershell
cd c:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system

# Check Python syntax
python -m py_compile src\failover\failover.py
python -m py_compile src\server_cluster.py
python -m py_compile src\consensus\consensus.py
python -m py_compile src\message_storage\storage.py
```

**Expected:** No output = SUCCESS ✅

---

## 🧪 Test 2: Manual Raft Test (2 minutes)

```powershell
python tests\test_manual_raft.py
```

**Expected output:**
```
************************************************************
  MANUAL RAFT CONSENSUS - TEST SUITE
  Author: ABEYRATHNA J G D A (IT23424432)
************************************************************

============================================================
TEST: Leader Election with 3 Nodes
============================================================

[1] Creating 3 Raft nodes...
[2] Starting all nodes...
[3] Waiting for leader election (5 seconds)...
[4] Election Results:
------------------------------------------------------------
Node 1:     leader | Term: 1 | Leader: 127.0.0.1:5000
Node 2:   follower | Term: 1 | Leader: 127.0.0.1:5000
Node 3:   follower | Term: 1 | Leader: 127.0.0.1:5000

[5] Verification:
  - Number of leaders: 1
  - Leader(s): ['127.0.0.1:5000']
  ✓ SUCCESS: Exactly one leader elected
  ✓ SUCCESS: All nodes agree on leader

============================================================
TEST COMPLETE
============================================================
```

**If you see this, consensus works!** ✅

---

## 🧪 Test 3: Full System Test (5 minutes)

### Step 1: Start Server Nodes

**Terminal 1:**
```powershell
cd c:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system\src
python server_cluster.py
```

**Terminal 2:**
```powershell
cd c:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system\src
python server_cluster.py --port 5001
```

**Terminal 3:**
```powershell
cd c:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system\src
python server_cluster.py --port 5002
```

### Step 2: Verify Leader Election

**Look for these logs in the terminals:**

```
✅ GOOD LOGS (should see):
[RAFT] Node 127.0.0.1:5000 initialized (RPC port: 6000)
[RAFT] RPC server listening on port 6000
[Consensus] Using MANUAL Raft implementation (not raftos library)
[RAFT] Node 127.0.0.1:5000 starting election for term 1
[RAFT] ✓ Node 127.0.0.1:5000 became LEADER for term 1
[Consensus] ✓ Node 127.0.0.1:5000 is now the LEADER
[Failover] Initial leader is 127.0.0.1:5000
Server started successfully on 127.0.0.1:5000
```

```
❌ BAD LOGS (should NOT see):
NameError: name 'raftos' is not defined
ImportError: No module named 'raftos'
AttributeError: module 'raftos' has no attribute 'get_leader'
```

### Step 3: Test Client Connection

**Terminal 4:**
```powershell
cd c:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system\src
python client.py
```

**Actions:**
1. Enter a username when prompted
2. Type a message and press Enter
3. Verify message appears in other client (if you have one)

**Expected:**
```
Connected to server at 127.0.0.1:5000
Enter your username: testuser
Welcome to the Distributed Messaging System!
You: Hello World!
[Message sent successfully]
```

---

## 🧪 Test 4: Failover Test (3 minutes)

### Step 1: Identify Current Leader

Look at the server terminal logs to find which node is leader:
```
[Consensus] ✓ Node 127.0.0.1:5000 is now the LEADER
```

### Step 2: Kill the Leader

Press `Ctrl+C` in the leader's terminal

### Step 3: Watch Other Nodes

**Expected logs in remaining nodes:**
```
[RAFT] Node 127.0.0.1:5001 election timeout, starting election
[RAFT] Node 127.0.0.1:5001 starting election for term 2
[RAFT] ✓ Node 127.0.0.1:5001 became LEADER for term 2
[Consensus] ✓ Node 127.0.0.1:5001 is now the LEADER
[Failover] Leader changed from 127.0.0.1:5000 to 127.0.0.1:5001
```

**Timing:** New leader should be elected within 500ms ✅

### Step 4: Verify Client Reconnects

**Expected in client terminal:**
```
Connection lost. Attempting to reconnect...
Reconnected to 127.0.0.1:5001
```

---

## 🐛 Troubleshooting

### Problem: "NameError: raftos is not defined"

**Solution:**
```powershell
# Re-check files were updated correctly
cd c:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system
python -c "import src.consensus.consensus; print('OK')"
```

If error persists, check these files:
- `src/failover/failover.py` - Line 5 should NOT have `import raftos`
- `src/server_cluster.py` - Line ~11 should NOT have `import raftos`
- `src/server.py` - Should NOT have `import raftos`

---

### Problem: "Consensus manager initialized with 0 nodes"

**Cause:** cluster_nodes list is empty

**Solution:** Make sure you're running `server_cluster.py` (not `server.py`)

---

### Problem: "Address already in use"

**Cause:** Port 5000/5001/5002 already in use

**Solution:**
```powershell
# Find and kill process using port
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

### Problem: No leader elected after 10 seconds

**Cause:** Firewall blocking localhost connections

**Solution:**
1. Check Windows Firewall
2. Allow Python through firewall
3. Test with simpler command:
   ```powershell
   python tests\test_manual_raft.py
   ```

---

## ✅ Success Criteria

Your system is working correctly if:

- [ ] `test_manual_raft.py` shows "✓ SUCCESS: Exactly one leader elected"
- [ ] Server logs show `[RAFT] ✓ Node became LEADER`
- [ ] Server logs show `[Consensus] Using MANUAL Raft implementation`
- [ ] **NO** `raftos` errors appear
- [ ] Client can connect and send messages
- [ ] When leader killed, new leader elected within 500ms
- [ ] Client automatically reconnects to new leader

---

## 📸 Screenshot Checklist (for Report)

Take screenshots showing:

1. **Manual Raft test output:**
   - ✓ SUCCESS: Exactly one leader elected
   - ✓ SUCCESS: All nodes agree on leader

2. **Server startup logs:**
   - [RAFT] Node initialized
   - [RAFT] became LEADER
   - [Consensus] Using MANUAL Raft implementation

3. **Failover test:**
   - Leader changed from X to Y
   - New leader elected

4. **Client connection:**
   - Connected to server
   - Messages sent successfully
   - Reconnection after failover

---

## 🎯 Quick Verification Commands

```powershell
# 1. Check no raftos imports
cd c:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system
findstr /s /i "import raftos" src\*.py
# Should only find consensu-sE.py (old unused file)

# 2. Check manual Raft exists
dir src\consensus\raft_node.py
# Should show file with ~560 lines

# 3. Run quick test
python tests\test_manual_raft.py
# Should show SUCCESS messages

# 4. Check syntax
python -m py_compile src\server_cluster.py
# Should have no output (success)
```

---

## 🚀 You're Ready!

If all tests pass:
- ✅ raftos completely removed
- ✅ Manual Raft working
- ✅ All components integrated
- ✅ Failover working
- ✅ Ready for demonstration

**Your system is now 100% library-independent for consensus!** 🎉

---

## 📝 What to Tell Your Professor

**Q: "Did you implement consensus yourself?"**

**A:** "Yes, we implemented the Raft consensus algorithm manually in 
`raft_node.py` (560 lines). It includes leader election, heartbeat 
mechanism, RequestVote RPC, AppendEntries RPC, and thread-safe state 
management. We can demonstrate it working with our test suite and 
explain the algorithm's internals."

**Show them:**
1. `tests/test_manual_raft.py` running
2. Source code in `src/consensus/raft_node.py`
3. Live demo with 3 servers + failover
4. Documentation explaining design decisions

**Perfect!** ✅

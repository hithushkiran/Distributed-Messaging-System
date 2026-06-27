# 🧪 Complete Manual Testing Guide
## Test Every Component with Exact Commands

**Purpose:** Step-by-step manual testing of all 4 components  
**Time:** 30-40 minutes (complete testing)  
**Prerequisites:** Virtual environment activated, project directory

---

## 📋 Pre-Testing Setup

```powershell
# Navigate to project
cd C:\Users\User\Downloads\DS-IMPORT\distributed-messaging-system

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Clean logs and state
Remove-Item full_system.log -ErrorAction SilentlyContinue
Remove-Item -Path src\logs\* -Recurse -Force -ErrorAction SilentlyContinue
New-Item -Path src\logs\0 -ItemType Directory -Force
New-Item -Path src\logs\1 -ItemType Directory -Force
New-Item -Path src\logs\2 -ItemType Directory -Force

# Clear terminal
Clear-Host
```

---

## ✅ TEST 1: Unit Tests (All Components)

### Test 1.1: Run All Unit Tests

**Command:**
```powershell
python tests/test_all_members_simple.py
```

**Expected Output:**
```
test_consensus_initialization (test_member4_individual.TestMember4Consensus) ... ok
test_failover_initialization (test_member1_individual.TestMember1Failover) ... ok
test_health_check_initialization (test_member1_individual.TestMember1Failover) ... ok
test_leader_status_tracking (test_member1_individual.TestMember1Failover) ... ok
test_message_deduplication (test_member2_individual.TestMember2Storage) ... ok
test_message_retrieval (test_member2_individual.TestMember2Storage) ... ok
test_message_storage (test_member2_individual.TestMember2Storage) ... ok
test_offset_calculation (test_member3_individual.TestMember3TimeSync) ... ok
test_storage_initialization (test_member2_individual.TestMember2Storage) ... ok
test_storage_with_replication (test_member2_individual.TestMember2Storage) ... ok
test_synchronized_timestamp (test_member3_individual.TestMember3TimeSync) ... ok
test_timesync_initialization (test_member3_individual.TestMember3TimeSync) ... ok
... (more tests)

----------------------------------------------------------------------
Ran 19 tests in 0.232s

OK
```

**✅ Pass Criteria:** All 19 tests pass with "OK"  
**❌ Fail Criteria:** Any test fails or errors occur

---

### Test 1.2: Test Member 1 (Fault Tolerance) Individually

**Command:**
```powershell
python tests/test_member1_individual.py
```

**Expected Output:**
```
test_failover_initialization ... ok
test_health_check_initialization ... ok
test_leader_status_tracking ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK
```

**✅ Pass Criteria:** 3/3 tests pass  
**What This Tests:**
- Health checker initialization
- Leader status tracking
- Failover detection mechanisms

---

### Test 1.3: Test Member 2 (Message Storage) Individually

**Command:**
```powershell
python tests/test_member2_individual.py
```

**Expected Output:**
```
test_message_deduplication ... ok
test_message_retrieval ... ok
test_message_storage ... ok
test_storage_initialization ... ok
test_storage_with_replication ... ok
test_concurrent_storage ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.016s

OK
```

**✅ Pass Criteria:** 6/6 tests pass  
**What This Tests:**
- Storage initialization
- Message storage operations
- Message retrieval with filtering
- Deduplication logic
- Replication coordination
- Concurrent access safety

---

### Test 1.4: Test Member 3 (Time Synchronization) Individually

**Command:**
```powershell
python tests/test_member3_individual.py
```

**Expected Output:**
```
test_offset_calculation ... ok
test_synchronized_timestamp ... ok
test_timesync_initialization ... ok
test_periodic_resynchronization ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.002s

OK
```

**✅ Pass Criteria:** 4/4 tests pass  
**What This Tests:**
- Time sync initialization
- Offset calculation accuracy
- Synchronized timestamp generation
- Periodic re-synchronization

---

### Test 1.5: Test Member 4 (Consensus) Individually

**Command:**
```powershell
python tests/test_member4_individual.py
```

**Expected Output:**
```
test_consensus_initialization ... ok
test_heartbeat_mechanism ... ok
test_leader_election ... ok
test_quorum_agreement ... ok
test_state_transitions ... ok
test_network_partition_handling ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.213s

OK
```

**✅ Pass Criteria:** 6/6 tests pass  
**What This Tests:**
- Raft consensus initialization
- Leader election process
- Heartbeat mechanism
- Quorum requirements
- State machine transitions
- Network partition handling

---

## 🚀 TEST 2: Cluster Formation & Leader Election

### Test 2.1: Start Single Node (No Quorum)

**Terminal 1:**
```powershell
python src/server_cluster.py 0
```

**Expected Output:**
```
======================================================================
DEMO MODE: Showing only important events (full logs in full_system.log)
======================================================================

19:00:00 [ClusterServer] INFO     Starting cluster node 0 on 127.0.0.1:5000
19:00:00 [Consensus    ] INFO     Initialized Raft node
19:00:00 [Consensus    ] INFO     Starting Raft consensus
```

**Wait 10 seconds and observe:**
- Node stays in CANDIDATE state
- Repeatedly attempts elections
- **No leader elected** (needs majority)

**✅ Pass Criteria:** 
- Server starts successfully
- No leader election (expected - no quorum)
- Node continuously attempts elections

**Keep this terminal running**

---

### Test 2.2: Add Second Node (Achieve Quorum)

**Terminal 2:**
```powershell
python src/server_cluster.py 1
```

**Expected Output:**
```
======================================================================
DEMO MODE: Showing only important events (full logs in full_system.log)
======================================================================

19:01:00 [ClusterServer] INFO     Starting cluster node 1 on 127.0.0.1:5001
19:01:00 [Consensus    ] INFO     Initialized Raft node
>>> 19:01:03 [Consensus    ] INFO     ELECTED AS LEADER FOR TERM 1
```

**OR** (in Terminal 1):
```
>>> 19:01:03 [Consensus    ] INFO     ELECTED AS LEADER FOR TERM 1
```

**✅ Pass Criteria:**
- Second node starts successfully
- **Leader is elected** within 10 seconds
- One node shows "ELECTED AS LEADER"
- Other node accepts the leader

**Note which port (5000 or 5001) is the leader**

**Keep both terminals running**

---

### Test 2.3: Add Third Node (Full Cluster)

**Terminal 3:**
```powershell
python src/server_cluster.py 2
```

**Expected Output:**
```
======================================================================
DEMO MODE: Showing only important events (full logs in full_system.log)
======================================================================

19:02:00 [ClusterServer] INFO     Starting cluster node 2 on 127.0.0.1:5002
19:02:00 [Consensus    ] INFO     Initialized Raft node
19:02:00 [Consensus    ] INFO     Became FOLLOWER - accepted leader
```

**✅ Pass Criteria:**
- Third node starts successfully
- Immediately becomes FOLLOWER
- Discovers existing leader
- No re-election triggered

**Cluster Status:** ✅ 3 nodes, 1 leader, 2 followers

**Keep all three terminals running**

---

### Test 2.4: Verify Cluster Status

**Terminal 4:**
```powershell
# Check status on any node (replace 5000 with your leader port)
curl http://localhost:5000/status
```

**Expected Output:**
```json
{
  "node_id": "127.0.0.1:5000",
  "state": "LEADER",
  "term": 1,
  "leader": "127.0.0.1:5000",
  "healthy_nodes": ["127.0.0.1:5000", "127.0.0.1:5001", "127.0.0.1:5002"],
  "message_count": 0
}
```

**Check all three nodes:**
```powershell
curl http://localhost:5000/status
curl http://localhost:5001/status
curl http://localhost:5002/status
```

**✅ Pass Criteria:**
- All nodes report same leader
- All nodes report same term
- healthy_nodes shows all 3 nodes
- One node shows state: "LEADER"
- Two nodes show state: "FOLLOWER"

---

## 📤 TEST 3: Message Storage & Replication

### Test 3.1: Send Single Message

**Terminal 4:**
```powershell
# Send to leader (replace 5000 with your leader port)
python src/client.py 5000 "Test message 1" Alice
```

**Expected Output:**
```
✓ Message sent successfully!
Message ID: msg_1696600000123_001
```

**Watch Server Terminals:**
- Leader should show: "MESSAGE STORED"
- Followers should show: "MESSAGE REPLICATED"

**✅ Pass Criteria:**
- Client receives success confirmation
- Message ID returned
- Leader logs message storage
- Followers receive replication

---

### Test 3.2: Verify Message on All Nodes

**Terminal 4:**
```powershell
# Query all three nodes
curl http://localhost:5000/messages
curl http://localhost:5001/messages
curl http://localhost:5002/messages
```

**Expected Output (all three should be identical):**
```json
{
  "count": 1,
  "messages": [
    {
      "message_id": "msg_1696600000123_001",
      "content": "Test message 1",
      "sender": "Alice",
      "timestamp": 1696600000.123,
      "term": 1
    }
  ]
}
```

**✅ Pass Criteria:**
- All three nodes return identical JSON
- count: 1
- Message content matches
- Sender is "Alice"
- Term is 1

---

### Test 3.3: Send Multiple Messages

**Terminal 4:**
```powershell
python src/client.py 5000 "Message 2" Bob
python src/client.py 5000 "Message 3" Charlie
python src/client.py 5000 "Message 4" Dave
python src/client.py 5000 "Message 5" Eve
```

**Expected Output (for each):**
```
✓ Message sent successfully!
Message ID: msg_...
```

**Verify replication:**
```powershell
curl http://localhost:5000/messages
```

**Expected:**
```json
{
  "count": 5,
  "messages": [
    {"message_id": "...", "content": "Test message 1", "sender": "Alice"},
    {"message_id": "...", "content": "Message 2", "sender": "Bob"},
    {"message_id": "...", "content": "Message 3", "sender": "Charlie"},
    {"message_id": "...", "content": "Message 4", "sender": "Dave"},
    {"message_id": "...", "content": "Message 5", "sender": "Eve"}
  ]
}
```

**✅ Pass Criteria:**
- All 5 messages accepted
- All nodes have count: 5
- Messages ordered by timestamp
- All nodes have identical data

---

### Test 3.4: Test Message Deduplication

**Terminal 4:**
```powershell
# Try to send to follower (should redirect to leader)
python src/client.py 5001 "Duplicate test" Frank
```

**Expected:**
- Client may redirect to leader automatically
- Message stored once (no duplicates)

**Verify:**
```powershell
curl http://localhost:5000/messages
```

**✅ Pass Criteria:**
- Message count increases by 1 only
- No duplicate entries

---

### Test 3.5: Test Interactive Client

**Terminal 4:**
```powershell
python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002
```

**Expected Output:**
```
Connected to server 127.0.0.1:5000
Enter your username: _
```

**Type:**
```
Interactive_User
```

**Then type messages:**
```
Hello from interactive mode!
Testing real-time messaging
Watching replication happen
```

**Press Ctrl+C to exit**

**Verify messages stored:**
```powershell
curl http://localhost:5000/messages
```

**✅ Pass Criteria:**
- Client connects successfully
- Can enter username
- Can send multiple messages
- All messages replicated to all nodes

---

## ⚠️ TEST 4: Fault Tolerance & Failover

### Test 4.1: Identify Current Leader

**Terminal 4:**
```powershell
curl http://localhost:5000/status
curl http://localhost:5001/status
curl http://localhost:5002/status
```

**Note which port shows:** `"state": "LEADER"`

**For this guide, assume port 5000 is leader**

---

### Test 4.2: Kill the Leader

**In the LEADER terminal (e.g., Terminal 1 if port 5000 is leader):**
```
Press: Ctrl+C
```

**Expected in Leader Terminal:**
```
Shutting down gracefully...
Server stopped.
```

**Expected in Follower Terminals (2 & 3):**
```
>>> WARNING  HEALTH CHECK FAILED: Leader not responding
>>> INFO     STARTING ELECTION FOR TERM 2
>>> INFO     ELECTED AS LEADER FOR TERM 2
```

**✅ Pass Criteria:**
- Leader shuts down cleanly
- Followers detect failure within 5 seconds
- New election starts automatically
- New leader elected within 10 seconds
- Term increases (was 1, now 2)

**Note the new leader port**

---

### Test 4.3: Verify Cluster After Failover

**Terminal 4:**
```powershell
# Check new leader status (use new leader port, e.g., 5001)
curl http://localhost:5001/status
```

**Expected:**
```json
{
  "node_id": "127.0.0.1:5001",
  "state": "LEADER",
  "term": 2,
  "leader": "127.0.0.1:5001",
  "healthy_nodes": ["127.0.0.1:5001", "127.0.0.1:5002"],
  "message_count": 8
}
```

**✅ Pass Criteria:**
- New leader identified
- Term increased to 2
- Only 2 healthy nodes (failed node missing)
- Message count unchanged (no data loss)

---

### Test 4.4: Verify No Data Loss

**Terminal 4:**
```powershell
# Query new leader for messages
curl http://localhost:5001/messages
```

**Expected:**
```json
{
  "count": 8,
  "messages": [
    ... (all 8 previous messages still present)
  ]
}
```

**✅ Pass Criteria:**
- All 8 messages still present
- No messages lost during failover
- Messages in correct order

---

### Test 4.5: Send Messages to New Leader

**Terminal 4:**
```powershell
# Send to new leader (use new leader port)
python src/client.py 5001 "After failover message 1" Grace
python src/client.py 5001 "After failover message 2" Henry
```

**Expected:**
```
✓ Message sent successfully!
```

**Verify:**
```powershell
curl http://localhost:5001/messages
```

**Expected:**
```json
{
  "count": 10,
  "messages": [
    ... (8 old messages)
    {"content": "After failover message 1", "sender": "Grace", "term": 2},
    {"content": "After failover message 2", "sender": "Henry", "term": 2}
  ]
}
```

**✅ Pass Criteria:**
- New messages accepted by new leader
- Messages replicated to remaining follower
- Term is 2 for new messages
- Total count: 10

---

### Test 4.6: Restart Failed Node

**In the previously failed terminal (Terminal 1):**
```powershell
python src/server_cluster.py 0
```

**Expected Output:**
```
19:15:00 [ClusterServer] INFO     Starting cluster node 0 on 127.0.0.1:5000
19:15:00 [Consensus    ] INFO     Initialized Raft node
>>> 19:15:03 [Consensus    ] INFO     Became FOLLOWER - accepted leader 127.0.0.1:5001
>>> 19:15:05 [Storage      ] INFO     SYNCING DATA FROM LEADER
>>> 19:15:06 [Storage      ] INFO     RECEIVED 10 MESSAGES FROM LEADER
```

**✅ Pass Criteria:**
- Node restarts successfully
- Discovers current leader (5001)
- Becomes FOLLOWER
- Syncs missing data
- Receives all 10 messages

---

### Test 4.7: Verify Full Recovery

**Terminal 4:**
```powershell
# Check cluster status
curl http://localhost:5001/status
```

**Expected:**
```json
{
  "healthy_nodes": ["127.0.0.1:5000", "127.0.0.1:5001", "127.0.0.1:5002"],
  "message_count": 10
}
```

**Verify recovered node has all data:**
```powershell
curl http://localhost:5000/messages
```

**Expected:**
```json
{
  "count": 10,
  "messages": [... all 10 messages ...]
}
```

**✅ Pass Criteria:**
- All 3 nodes healthy again
- Recovered node has all 10 messages
- All nodes have identical data
- Cluster fully operational

---

## 🕐 TEST 5: Time Synchronization

### Test 5.1: Check Time Sync Initialization

**Watch Server Terminals during startup:**

**Expected logs:**
```
19:00:00 [TimeSync] INFO     Initialized time synchronization
19:00:00 [TimeSync] INFO     Syncing with leader 127.0.0.1:5000
19:00:01 [TimeSync] INFO     Time offset calculated: 0.001234s
```

**✅ Pass Criteria:**
- Time sync starts on all nodes
- Followers sync with leader
- Offset calculated successfully

---

### Test 5.2: Verify Message Timestamps

**Terminal 4:**
```powershell
curl http://localhost:5000/messages
```

**Check timestamps in response:**
```json
{
  "messages": [
    {"timestamp": 1696600000.123, ...},
    {"timestamp": 1696600001.456, ...},
    {"timestamp": 1696600002.789, ...}
  ]
}
```

**✅ Pass Criteria:**
- All timestamps are monotonically increasing
- Timestamps are consistent across all nodes
- No timestamp collisions

---

### Test 5.3: Test Message Ordering

**Terminal 4:**
```powershell
# Send messages rapidly
python src/client.py 5001 "A" User
python src/client.py 5001 "B" User
python src/client.py 5001 "C" User
python src/client.py 5001 "D" User
python src/client.py 5001 "E" User
```

**Verify order:**
```powershell
curl http://localhost:5000/messages
```

**✅ Pass Criteria:**
- Messages appear in order: A, B, C, D, E
- Timestamps increase monotonically
- No out-of-order messages

---

## 🔄 TEST 6: Network Partition Simulation

### Test 6.1: Create 2-1 Partition

**Kill one follower (e.g., Terminal 3, port 5002):**
```
Press: Ctrl+C in Terminal 3
```

**Expected in remaining terminals:**
```
>>> WARNING  HEALTH CHECK FAILED: Node 2 not responding
```

**✅ Pass Criteria:**
- Partition detected
- Majority still available (2/3 nodes)
- Leader remains operational

---

### Test 6.2: Test Write Availability

**Terminal 4:**
```powershell
# Send to leader (should work - majority available)
python src/client.py 5001 "Partition test message" Iris
```

**Expected:**
```
✓ Message sent successfully!
```

**✅ Pass Criteria:**
- Message accepted (majority available)
- Leader continues operating
- Message replicated to available follower

---

### Test 6.3: Recover from Partition

**Restart node 2:**
```powershell
python src/server_cluster.py 2
```

**Expected:**
```
>>> 19:20:00 [Consensus] INFO Became FOLLOWER
>>> 19:20:02 [Storage  ] INFO SYNCING DATA FROM LEADER
>>> 19:20:03 [Storage  ] INFO RECEIVED 11 MESSAGES
```

**Verify:**
```powershell
curl http://localhost:5002/messages
```

**✅ Pass Criteria:**
- Node rejoins cluster
- Syncs missing message
- All nodes have 11 messages now

---

## 🎯 TEST 7: Stress Testing

### Test 7.1: Rapid Message Submission

**Terminal 4:**
```powershell
# Send 20 messages rapidly
for ($i=1; $i -le 20; $i++) {
    python src/client.py 5001 "Stress test message $i" StressUser
}
```

**Expected:**
```
✓ Message sent successfully! (x20)
```

**Verify:**
```powershell
curl http://localhost:5000/messages
```

**✅ Pass Criteria:**
- All 20 messages accepted
- No messages lost
- All nodes have count: 31 (11 + 20)
- Messages in correct order

---

### Test 7.2: Concurrent Clients

**Terminal 4:**
```powershell
# Start 3 clients in parallel
Start-Job { python src/client.py 5001 "Client 1 message" User1 }
Start-Job { python src/client.py 5001 "Client 2 message" User2 }
Start-Job { python src/client.py 5001 "Client 3 message" User3 }

# Wait for jobs to complete
Get-Job | Wait-Job

# Check results
Get-Job | Receive-Job
```

**Expected:**
```
✓ Message sent successfully! (x3)
```

**Verify:**
```powershell
curl http://localhost:5000/messages
```

**✅ Pass Criteria:**
- All 3 concurrent messages accepted
- No race conditions
- All nodes have count: 34

---

### Test 7.3: Leader Failure During High Load

**Terminal 4 (start rapid sending in background):**
```powershell
Start-Job -ScriptBlock {
    for ($i=1; $i -le 50; $i++) {
        python src/client.py 5001 "Load test $i" LoadUser
        Start-Sleep -Milliseconds 100
    }
}
```

**After 2 seconds, kill the leader (Terminal with port 5001):**
```
Press: Ctrl+C in leader terminal
```

**Wait for re-election and job completion:**
```powershell
Get-Job | Wait-Job
Get-Job | Receive-Job
```

**Verify:**
```powershell
# Find new leader and check messages
curl http://localhost:5000/status
curl http://localhost:5002/status

# Count messages
curl http://localhost:5000/messages
```

**✅ Pass Criteria:**
- New leader elected automatically
- Most messages successfully delivered
- No silent data loss (failed messages return errors)
- System recovers and continues accepting messages

---

## 📊 TEST 8: System Monitoring

### Test 8.1: Monitor Full Logs

**Terminal 5:**
```powershell
Get-Content full_system.log -Wait -Tail 50
```

**✅ Pass Criteria:**
- Logs updating in real-time
- All events captured
- Timestamps consistent

---

### Test 8.2: Search for Events

**Terminal 4:**
```powershell
# Search for leader elections
Select-String "LEADER|ELECTION" full_system.log

# Search for failures
Select-String "FAILED|ERROR" full_system.log

# Search for messages
Select-String "MESSAGE STORED" full_system.log
```

**✅ Pass Criteria:**
- Can find all leader elections
- Can track failures
- Can see all message operations

---

### Test 8.3: Export Test Summary

**Terminal 4:**
```powershell
# Create test summary
$summary = @"
TEST SUMMARY - $(Get-Date)
============================

Total Messages Sent: $($(curl http://localhost:5000/messages -UseBasicParsing | ConvertFrom-Json).count)
Cluster Status: $($(curl http://localhost:5000/status -UseBasicParsing | ConvertFrom-Json).healthy_nodes.Count) / 3 nodes healthy
Current Leader: $($(curl http://localhost:5000/status -UseBasicParsing | ConvertFrom-Json).leader)
Current Term: $($(curl http://localhost:5000/status -UseBasicParsing | ConvertFrom-Json).term)
"@

$summary | Out-File test_summary.txt
Get-Content test_summary.txt
```

---

## 🧹 Cleanup After Testing

```powershell
# Stop all servers (press Ctrl+C in each terminal)

# Verify all stopped
Get-Process python -ErrorAction SilentlyContinue

# If any still running:
Get-Process python | Stop-Process -Force

# Verify ports are free
netstat -an | findstr "5000 5001 5002"

# Save logs for analysis
Copy-Item full_system.log -Destination "manual_test_logs_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Clean up for next test
Remove-Item full_system.log
Remove-Item -Path src\logs\* -Recurse -Force -ErrorAction SilentlyContinue
```

---

## ✅ Test Results Checklist

### Component Tests
- [ ] Member 1 (Fault Tolerance): 3/3 tests pass
- [ ] Member 2 (Message Storage): 6/6 tests pass
- [ ] Member 3 (Time Sync): 4/4 tests pass
- [ ] Member 4 (Consensus): 6/6 tests pass
- [ ] All Unit Tests: 19/19 tests pass

### Cluster Formation
- [ ] Single node starts (no leader)
- [ ] Two nodes form quorum (leader elected)
- [ ] Three nodes join cluster (full cluster)
- [ ] Cluster status verifiable

### Message Operations
- [ ] Single message stored and replicated
- [ ] Multiple messages handled correctly
- [ ] Message ordering maintained
- [ ] All nodes have identical data
- [ ] Interactive client works

### Fault Tolerance
- [ ] Leader failure detected
- [ ] Automatic re-election works
- [ ] Zero data loss after failover
- [ ] New leader accepts messages
- [ ] Failed node recovers and syncs

### Time Synchronization
- [ ] Time sync initializes
- [ ] Timestamps monotonically increase
- [ ] Message ordering preserved

### Stress Testing
- [ ] Rapid messages handled
- [ ] Concurrent clients work
- [ ] Failover during load succeeds

### Monitoring
- [ ] Logs captured correctly
- [ ] Events searchable
- [ ] Real-time monitoring works

---

## 📝 Test Report Template

```
DISTRIBUTED MESSAGING SYSTEM - MANUAL TEST REPORT
Date: [Date]
Tester: [Your Name]
Duration: [Time]

UNIT TESTS:
- Member 1: PASS ✓ / FAIL ✗
- Member 2: PASS ✓ / FAIL ✗
- Member 3: PASS ✓ / FAIL ✗
- Member 4: PASS ✓ / FAIL ✗

INTEGRATION TESTS:
- Cluster Formation: PASS ✓ / FAIL ✗
- Message Replication: PASS ✓ / FAIL ✗
- Leader Election: PASS ✓ / FAIL ✗
- Fault Recovery: PASS ✓ / FAIL ✗
- Time Synchronization: PASS ✓ / FAIL ✗

STRESS TESTS:
- Rapid Messages: PASS ✓ / FAIL ✗
- Concurrent Clients: PASS ✓ / FAIL ✗
- Failover Under Load: PASS ✓ / FAIL ✗

ISSUES FOUND:
[List any issues discovered]

OVERALL RESULT: PASS ✓ / FAIL ✗
```

---

**🎉 Complete Manual Testing Guide - All Components Covered!**

**Estimated Time:**
- Quick Test (Tests 1-4): 15 minutes
- Complete Test (Tests 1-8): 40 minutes
- Full Analysis: 60 minutes

**Next Steps After Testing:**
1. Document any failures
2. Save test logs
3. Create screenshots for report
4. Update test checklist
5. Prepare demo based on working tests

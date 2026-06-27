# Comprehensive Testing Guide for Distributed Messaging System

## Testing Strategy Overview

This guide provides step-by-step testing procedures for each component and integration testing scenarios.

---

## 1. FAULT TOLERANCE TESTING (Member 1: IT23184558)

### Test 1.1: Basic Health Check Functionality
**Purpose:** Verify TCP-based health checks work correctly

**Steps:**
```powershell
# Terminal 1: Start first server
cd src
python server_cluster.py 0

# Terminal 2: Start second server
cd src
python server_cluster.py 1

# Terminal 3: Start third server
cd src
python server_cluster.py 2
```

**Expected Result:**
- All three servers should start successfully
- Logs should show "Node X is now healthy" for other nodes
- No failure warnings should appear

**Verification:**
- Check logs for "Failover handler initialized with 3 nodes"
- Verify "Failover monitoring started" appears in logs

---

### Test 1.2: Node Failure Detection
**Purpose:** Test automatic failure detection when a node goes down

**Steps:**
```powershell
# 1. Start all three servers (as in Test 1.1)
# 2. Wait 10 seconds for cluster to stabilize
# 3. In Terminal 2, press Ctrl+C to kill server 1
```

**Expected Result:**
- Within 3-5 seconds, other servers should log: "Node 127.0.0.1:5001 appears to be down"
- Healthy nodes should continue operating
- Client connections to failed node should trigger reconnection

**Verification:**
- Check failover logs for node down warnings
- Verify healthy_nodes set is updated (check via logs)
- Confirm leader election occurs if leader failed

---

### Test 1.3: Client Reconnection After Server Failure
**Purpose:** Test client automatic reconnection to healthy nodes

**Steps:**
```powershell
# 1. Start all three servers
# 2. Terminal 4: Start client
cd src
python client.py

# 3. Enter username and send a message
# 4. Note which server client is connected to (check client logs)
# 5. Kill that specific server
```

**Expected Result:**
- Client should log "Lost connection to server"
- Client should log "Attempting to reconnect..."
- Client should automatically connect to another healthy server
- Client should resend login message
- Any queued messages should be delivered

**Verification:**
- Check for "Connected to server 127.0.0.1:XXXX" after reconnection
- Verify no messages were lost
- Confirm username re-registration

---

### Test 1.4: Node Recovery
**Purpose:** Test automatic node recovery when it comes back online

**Steps:**
```powershell
# 1. Start all servers
# 2. Kill server 1 (Ctrl+C in Terminal 2)
# 3. Wait 10 seconds
# 4. Restart server 1
cd src
python server_cluster.py 1
```

**Expected Result:**
- Other servers should detect recovered node within 3-5 seconds
- Logs should show "Node 127.0.0.1:5001 is now healthy"
- Node should rejoin cluster and synchronize state
- Raft should include it in consensus

**Verification:**
- Check failover logs for recovery message
- Verify node can receive messages
- Confirm node participates in Raft consensus

---

### Test 1.5: Message Queue During Failover
**Purpose:** Verify messages are queued and delivered after reconnection

**Steps:**
```powershell
# 1. Start all servers and one client
# 2. Kill the server client is connected to
# 3. Immediately type several messages in client (while disconnected)
# 4. Wait for reconnection
```

**Expected Result:**
- Messages typed during disconnection should be queued
- After reconnection, all queued messages should be sent automatically
- Other clients should receive all messages in correct order

**Verification:**
- Check client logs for "Message failed to send" followed by queue operations
- Verify all messages appear on other clients
- Confirm timestamp order is preserved

---

## 2. DATA REPLICATION & CONSISTENCY TESTING (Member 2: IT23398184)

### Test 2.1: Basic Message Storage
**Purpose:** Verify messages are stored in distributed storage

**Steps:**
```powershell
# 1. Start all three servers
# 2. Start a client and send a test message
# 3. Check server logs for storage confirmation
```

**Expected Result:**
- Log should show "Message stored with ID: XXXXX"
- Message ID format should be: {timestamp}_{username}_{type}
- All servers should have the message (check via Raft replication)

**Verification:**
- Search logs for "Message stored:"
- Verify Raft commit messages
- Check message appears in all server logs

---

### Test 2.2: Message Retrieval
**Purpose:** Test retrieving stored messages

**Steps:**
```python
# Add this test code to server_cluster.py temporarily:
async def test_retrieval():
    storage = MessageStorage()
    
    # Store test message
    test_id = f"{int(time.time())}_testuser_chat"
    test_msg = json.dumps({"content": "test", "sender": "testuser"})
    await storage.store_message(test_id, test_msg)
    
    # Retrieve message
    retrieved = await storage.get_message(test_id)
    print(f"Retrieved: {retrieved}")
    
    # Get all messages
    all_msgs = await storage.get_all_messages()
    print(f"Total messages: {len(all_msgs)}")

# Run in server startup
self.loop.run_until_complete(test_retrieval())
```

**Expected Result:**
- Test message should be retrieved successfully
- Retrieved content should match stored content
- All messages should be returned by get_all_messages()

---

### Test 2.3: Deduplication
**Purpose:** Verify duplicate messages are handled correctly

**Steps:**
```python
# Add to test code:
async def test_deduplication():
    storage = MessageStorage()
    
    # Store same message twice
    msg_id = "1234567890_testuser_chat"
    msg1 = json.dumps({"content": "test1"})
    msg2 = json.dumps({"content": "test2"})
    
    await storage.store_message(msg_id, msg1)
    await storage.store_message(msg_id, msg2)  # Duplicate ID
    
    # Retrieve
    result = await storage.get_message(msg_id)
    print(f"Final content: {result}")
```

**Expected Result:**
- Second message should overwrite first (since same ID)
- Only one message should exist with that ID
- Content should be from second store operation

---

### Test 2.4: Quorum-Based Consistency
**Purpose:** Test that messages require quorum to be stored

**Steps:**
```powershell
# 1. Start 3 servers
# 2. Start a client and send message
# 3. Quickly kill 2 servers (leave only 1 running)
# 4. Try to send another message
```

**Expected Result:**
- First message (with quorum) should succeed
- Second message (without quorum) should fail or timeout
- When quorum is restored, operations should resume

**Verification:**
- Check for Raft "no quorum" errors in logs
- Verify message storage fails without quorum
- Confirm automatic recovery when quorum restored

---

### Test 2.5: Replication Across Nodes
**Purpose:** Verify all nodes have same messages

**Steps:**
```powershell
# 1. Start all 3 servers
# 2. Send 10 messages from client
# 3. Kill servers one by one
# 4. Check logs from each server before killing
```

**Expected Result:**
- All servers should log the same message IDs
- Message order should be identical across servers
- Each server should have all 10 messages

**Verification:**
- Compare log files from each server
- Count message storage events (should match)
- Verify Raft indices are synchronized

---

## 3. TIME SYNCHRONIZATION TESTING (Member 3: IT23424432)

### Test 3.1: NTP Synchronization
**Purpose:** Verify successful NTP synchronization

**Steps:**
```powershell
# 1. Start server with NTP debugging
cd src
python server_cluster.py 0

# 2. Check logs for NTP sync messages
```

**Expected Result:**
- Log should show "Attempting to sync time with pool.ntp.org"
- Log should show "Time synchronized with [server], offset: X.XXX seconds"
- Offset value should be reasonable (< 1 second typically)

**Verification:**
- Search logs for "Time synchronized"
- Note the offset value
- Verify periodic re-sync occurs (every 1 hour)

---

### Test 3.2: Timestamp Consistency
**Purpose:** Test that all messages have accurate synchronized timestamps

**Steps:**
```powershell
# 1. Start all servers
# 2. Start two clients on different machines (or VMs with different local times)
# 3. Send messages from both clients rapidly
# 4. Compare timestamps in logs
```

**Expected Result:**
- All timestamps should be based on NTP time (not local time)
- Timestamps should increase monotonically
- Time differences between consecutive messages should be realistic

**Verification:**
- Extract timestamps from all messages
- Calculate time differences
- Verify no backwards time jumps

---

### Test 3.3: Clock Skew Handling
**Purpose:** Test system behavior with local clock skew

**Steps:**
```powershell
# 1. Manually adjust system time on one server machine
# (Move time forward/backward by 5 minutes)
# 2. Start that server
# 3. Send messages
# 4. Compare timestamps with other servers
```

**Expected Result:**
- Despite local clock skew, NTP offset should correct it
- Timestamps should be consistent across servers
- No out-of-order message issues

**Verification:**
- Check offset calculation in logs
- Verify timestamp accuracy
- Confirm message ordering is correct

---

### Test 3.4: Periodic Re-synchronization
**Purpose:** Verify periodic NTP re-sync works

**Steps:**
```powershell
# 1. Start server
# 2. Monitor logs for 1+ hours
# 3. Look for re-sync messages
```

**Expected Result:**
- Initial sync within first 60 seconds
- Re-sync every 60 minutes (3600 seconds)
- Only log if offset changes > 100ms

**Verification:**
- Count re-sync events in logs
- Verify timing matches expected intervals
- Check offset changes are logged appropriately

---

### Test 3.5: Fallback NTP Servers
**Purpose:** Test fallback to alternate NTP servers

**Steps:**
```python
# Modify timesync.py temporarily:
self.ntp_servers = [
    'invalid.server.com',  # This will fail
    'pool.ntp.org',        # This should succeed
    'time.google.com'
]
```

**Expected Result:**
- First server should fail with warning
- Second server should succeed
- System should continue with successful sync

**Verification:**
- Check logs for "Failed to sync with invalid.server.com"
- Verify "Time synchronized with pool.ntp.org" appears
- Confirm system is operational

---

## 4. CONSENSUS & AGREEMENT TESTING (Member 4: IT23424432)

### Test 4.1: Leader Election
**Purpose:** Verify Raft leader election works

**Steps:**
```powershell
# 1. Start all 3 servers
# 2. Check which one becomes leader
# 3. Wait for election to complete (5-10 seconds)
```

**Expected Result:**
- One server should be elected leader
- Log should show "This node is now the leader" on leader
- Other nodes should show follower status
- All nodes should agree on same leader

**Verification:**
- Check consensus logs for "Leader changed to: 127.0.0.1:XXXX"
- Verify get_leader() returns same value on all nodes
- Confirm only one leader exists

---

### Test 4.2: Leader Failover
**Purpose:** Test new leader election when current leader fails

**Steps:**
```powershell
# 1. Start all 3 servers
# 2. Identify current leader (check logs)
# 3. Kill the leader server
# 4. Observe election process
```

**Expected Result:**
- Followers should detect leader failure
- New election should start within seconds
- New leader should be elected
- System should continue operating

**Verification:**
- Check for "Leader changed from X to Y" in logs
- Verify new leader accepts writes
- Confirm message storage continues working

---

### Test 4.3: Split-Brain Prevention
**Purpose:** Verify system handles network partitions correctly

**Steps:**
```powershell
# 1. Start 3 servers on different machines/VMs
# 2. Use firewall rules to partition network:
#    - Partition 1: Server 0 (minority)
#    - Partition 2: Server 1 & 2 (majority)
# 3. Try to send messages to each partition
```

**Expected Result:**
- Majority partition (2 nodes) should elect leader and accept writes
- Minority partition (1 node) should reject writes (no quorum)
- No split-brain scenario should occur

**Verification:**
- Check that only majority partition is operational
- Verify minority partition logs "no quorum" errors
- Confirm no data divergence

---

### Test 4.4: Log Consistency
**Purpose:** Verify all nodes maintain consistent Raft logs

**Steps:**
```powershell
# 1. Start all servers
# 2. Send 20 messages
# 3. Check Raft log files on each server
```

**Expected Result:**
- All log files should have same entries
- Log indices should match
- Commit indices should be consistent

**Verification:**
```powershell
# Compare log files
cd logs
Compare-Object (Get-Content 0\log.txt) (Get-Content 1\log.txt)
Compare-Object (Get-Content 1\log.txt) (Get-Content 2\log.txt)
```

---

### Test 4.5: Consensus Performance
**Purpose:** Measure consensus latency under load

**Steps:**
```python
# Create performance test script:
import time
import asyncio
from message_storage.storage import MessageStorage

async def perf_test():
    storage = MessageStorage()
    
    start = time.time()
    for i in range(100):
        msg_id = f"{int(time.time())}_{i}_test"
        await storage.store_message(msg_id, f'{{"content":"msg{i}"}}')
    end = time.time()
    
    print(f"100 messages stored in {end-start:.2f} seconds")
    print(f"Average latency: {(end-start)/100*1000:.2f}ms per message")

asyncio.run(perf_test())
```

**Expected Result:**
- Should measure actual consensus overhead
- Typical latency: 10-50ms per message in local network
- Higher latency in distributed environments

---

## 5. INTEGRATION TESTING (All Members)

### Test 5.1: Full System Test
**Purpose:** Test all components working together

**Steps:**
```powershell
# 1. Start all 3 servers
# 2. Start 3 clients
# 3. All clients send messages
# 4. Kill one server
# 5. Continue sending messages
# 6. Kill another server
# 7. Restart both servers
# 8. Continue testing
```

**Expected Result:**
- All components should work seamlessly
- Message delivery should continue during failures
- State should be consistent after recovery

---

### Test 5.2: Stress Test
**Purpose:** Test system under high load

**Steps:**
```python
# Create stress test script:
import threading

def send_messages(client_id):
    client = MessageClient()
    client.connect()
    for i in range(1000):
        client.send_message("chat", f"Message {i} from client {client_id}")

threads = []
for i in range(10):
    t = threading.Thread(target=send_messages, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

**Expected Result:**
- All messages should be delivered
- No data loss or corruption
- System should remain stable

---

## 6. GITHUB REPOSITORY STRATEGY FOR SEPARATE CONTRIBUTIONS

### Approach 1: Branch-Based Development (RECOMMENDED)

**Setup:**
```powershell
# Main repository
git init
git add .
git commit -m "Initial complete implementation"
git branch main

# Create branches for each member
git checkout -b member1-fault-tolerance
git checkout -b member2-data-replication  
git checkout -b member3-time-sync
git checkout -b member4-consensus
```

**Member 1 (Fault Tolerance) - Commits:**
```powershell
git checkout member1-fault-tolerance

# Commit 1: Initial structure
git add src/failover/__init__.py
git commit -m "Initialize failover module structure"

# Commit 2: Health check implementation
git add src/failover/failover.py  # Add _is_node_alive, _check_node_health
git commit -m "Implement TCP-based health check mechanism"

# Commit 3: Failover monitoring
# Update failover.py with _monitor_cluster
git commit -m "Add automatic failover detection and monitoring"

# Commit 4: Client reconnection
git add src/client.py  # Add reconnect() method
git commit -m "Implement client auto-reconnection logic"

# Commit 5: Documentation
git add docs/fault_tolerance.md
git commit -m "Add fault tolerance documentation and test cases"
```

**Member 2 (Data Replication) - Commits:**
```powershell
git checkout member2-data-replication

# Commit 1: Storage module structure
git add src/message_storage/__init__.py
git commit -m "Initialize message storage module"

# Commit 2: Basic storage operations
git add src/message_storage/storage.py  # store_message, get_message
git commit -m "Implement basic message storage with Raft replication"

# Commit 3: Deduplication
# Update storage.py with deduplication logic
git commit -m "Add message deduplication using unique IDs"

# Commit 4: Retrieval optimization
# Add get_all_messages, get_messages_since
git commit -m "Optimize message retrieval with indexing"

# Commit 5: Documentation
git add docs/data_replication.md
git commit -m "Add data replication documentation and consistency analysis"
```

**Member 3 (Time Synchronization) - Commits:**
```powershell
git checkout member3-time-sync

# Commit 1: Time sync module structure
git add src/time_sync/__init__.py
git commit -m "Initialize time synchronization module"

# Commit 2: NTP implementation
git add src/time_sync/timesync.py  # sync_time, get_synced_time
git commit -m "Implement NTP synchronization protocol"

# Commit 3: Periodic re-sync
# Add _periodic_sync method
git commit -m "Add periodic time re-synchronization"

# Commit 4: Timestamp integration
# Update server.py to use time_sync for timestamps
git commit -m "Integrate synchronized timestamps throughout system"

# Commit 5: Documentation
git add docs/time_synchronization.md
git commit -m "Add time sync documentation and clock skew analysis"
```

**Member 4 (Consensus) - Commits:**
```powershell
git checkout member4-consensus

# Commit 1: Consensus module structure
git add src/consensus/__init__.py
git commit -m "Initialize consensus module"

# Commit 2: Raft integration
git add src/consensus/consensus.py  # Basic Consensus class
git commit -m "Integrate Raft consensus algorithm"

# Commit 3: Leader election monitoring
# Add _monitor_leadership method
git commit -m "Implement leader election monitoring"

# Commit 4: Cluster configuration
# Update server_cluster.py with Raft setup
git commit -m "Configure Raft cluster with quorum-based agreement"

# Commit 5: Documentation
git add docs/consensus.md
git commit -m "Add consensus documentation and performance analysis"
```

### Approach 2: Separate Repositories (Alternative)

**Create 4 repositories:**
1. `distributed-messaging-fault-tolerance`
2. `distributed-messaging-data-replication`
3. `distributed-messaging-time-sync`
4. `distributed-messaging-consensus`

**Each member's repo contains:**
- Their specific module (e.g., `src/failover/`)
- Integration code showing how it connects
- Test scripts for their component
- Documentation for their part
- README explaining their contribution

---

## 7. AUTOMATED TESTING SCRIPT

Create `test_all.py`:

```python
import subprocess
import time
import sys

def test_component(component_name, test_function):
    print(f"\n{'='*60}")
    print(f"Testing {component_name}")
    print(f"{'='*60}")
    try:
        test_function()
        print(f"✓ {component_name} tests passed")
        return True
    except Exception as e:
        print(f"✗ {component_name} tests failed: {e}")
        return False

def test_failover():
    # Start servers
    servers = []
    for i in range(3):
        p = subprocess.Popen(['python', 'server_cluster.py', str(i)])
        servers.append(p)
        time.sleep(2)
    
    # Test health checks
    time.sleep(5)
    
    # Kill one server
    servers[1].kill()
    time.sleep(5)
    
    # Cleanup
    for p in servers:
        if p.poll() is None:
            p.kill()

def test_storage():
    # Add storage tests
    pass

def test_time_sync():
    # Add time sync tests
    pass

def test_consensus():
    # Add consensus tests
    pass

if __name__ == "__main__":
    results = []
    results.append(test_component("Fault Tolerance", test_failover))
    results.append(test_component("Data Replication", test_storage))
    results.append(test_component("Time Synchronization", test_time_sync))
    results.append(test_component("Consensus", test_consensus))
    
    print(f"\n{'='*60}")
    print(f"Test Summary: {sum(results)}/{len(results)} passed")
    print(f"{'='*60}")
```

---

## Testing Checklist

- [ ] All servers start without errors
- [ ] Client can connect to any server
- [ ] Messages are delivered to all clients
- [ ] Node failure is detected within 5 seconds
- [ ] Client reconnects automatically
- [ ] Messages are not lost during failover
- [ ] All nodes have same messages (consistency)
- [ ] Timestamps are synchronized across servers
- [ ] Leader election works correctly
- [ ] System operates with quorum (2/3 nodes)
- [ ] System rejects operations without quorum
- [ ] Failed nodes can rejoin cluster
- [ ] No data corruption under stress

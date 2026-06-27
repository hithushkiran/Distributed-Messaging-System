# Logic Issues Analysis & Solutions

## WHERE I FOUND YOUR NAMES AND IT NUMBERS

**Source:** `Instruct.txt` file in your project root

The file contains:
```
IT23184558 - D B Y BINUWARA - Fault tolerance
IT23294998 - PABASARA T D J - Time Synchronization  
IT23398184 - DINUJAYA K V T - Data Replication & Consistency
IT23424432 - ABEYRATHNA J G D A - Consensus Implementation
```

Note: There's an inconsistency - Member 3's IT number shows as IT23294998 in Instruct.txt but IT23424432 in other places. **Please verify correct IT numbers before submission.**

---

## IDENTIFIED LOGIC ISSUES

### Issue 1: Timeout Inconsistency (HIGH PRIORITY)
**Location:** `failover.py` and `client.py`

**Problem:**
- Health check timeout: 2 seconds
- Client connection timeout: 5 seconds  
- Health check interval: 3 seconds

**Scenario:**
If a server takes 3-4 seconds to respond:
- Health check marks it as dead (2s timeout exceeded)
- Client might successfully connect (5s timeout not exceeded)
- Client connects to "dead" server, then immediately loses connection
- Creates connection loop

**Solution:**
```python
# Option 1: Align timeouts
# failover.py
s.settimeout(5)  # Match client timeout

# Option 2: Add grace period
def _check_node_health(self):
    failed_checks = {}  # Track consecutive failures
    for node_addr in self.cluster_nodes:
        if not self._is_node_alive(node_addr):
            failed_checks[node_addr] = failed_checks.get(node_addr, 0) + 1
            if failed_checks[node_addr] >= 2:  # Require 2 consecutive failures
                self.healthy_nodes.remove(node_addr)
        else:
            failed_checks[node_addr] = 0
```

---

### Issue 2: Message Queue Overflow (MEDIUM PRIORITY)
**Location:** `client.py`

**Problem:**
```python
def send_message(self, message_type, content):
    if not self.connected:
        with self.message_lock:
            self.message_queue.append((message_type, content))  # No limit!
        return False
```

If client is disconnected for long time, queue grows unbounded.

**Solution:**
```python
def send_message(self, message_type, content):
    if not self.connected:
        with self.message_lock:
            if len(self.message_queue) < 100:  # Set max queue size
                self.message_queue.append((message_type, content))
            else:
                logger.warning("Message queue full, dropping oldest message")
                self.message_queue.pop(0)  # Remove oldest
                self.message_queue.append((message_type, content))
        return False
```

---

### Issue 3: JSON Parsing Buffer Issue (HIGH PRIORITY)
**Location:** `client.py` - `receive_messages()`

**Problem:**
```python
buffer = bytearray()
while self.running:
    chunk = self.client_socket.recv(4096)
    buffer.extend(chunk)
    
    try:
        message_data = buffer.decode('utf-8')
        message = json.loads(message_data)  # Assumes complete JSON
        buffer.clear()  # Clears even if partial
```

If JSON message is split across multiple TCP packets, parsing fails.

**Solution:**
```python
buffer = bytearray()
while self.running:
    chunk = self.client_socket.recv(4096)
    if not chunk:
        self.connected = False
        self.reconnect()
        continue
    
    buffer.extend(chunk)
    
    # Try to parse multiple complete JSON objects
    while True:
        try:
            # Attempt to decode
            message_str = buffer.decode('utf-8')
            
            # Try to find complete JSON
            decoder = json.JSONDecoder()
            message, idx = decoder.raw_decode(message_str)
            
            # Successfully parsed - process message
            self._process_message(message)
            
            # Remove processed message from buffer
            buffer = buffer[idx:].lstrip()
            
        except json.JSONDecodeError:
            # Incomplete JSON - wait for more data
            break
        except UnicodeDecodeError:
            # Invalid data - clear buffer
            buffer.clear()
            break
```

---

### Issue 4: Race Condition in Failover (MEDIUM PRIORITY)
**Location:** `failover.py`

**Problem:**
```python
def _check_node_health(self):
    for node_addr in self.cluster_nodes:
        healthy = self._is_node_alive(node_addr)
        
        if healthy and node_addr not in self.healthy_nodes:
            self.healthy_nodes.add(node_addr)  # Not thread-safe
        elif not healthy and node_addr in self.healthy_nodes:
            self.healthy_nodes.remove(node_addr)  # Not thread-safe
```

Multiple threads might access `healthy_nodes` simultaneously.

**Solution:**
```python
def __init__(self, cluster_nodes):
    self.cluster_nodes = cluster_nodes
    self.healthy_nodes = set(cluster_nodes)
    self.health_lock = threading.Lock()  # Add lock
    # ... rest of init

def _check_node_health(self):
    for node_addr in self.cluster_nodes:
        healthy = self._is_node_alive(node_addr)
        
        with self.health_lock:  # Protect set operations
            if healthy and node_addr not in self.healthy_nodes:
                self.healthy_nodes.add(node_addr)
                logger.info(f"Node {node_addr} is now healthy")
            elif not healthy and node_addr in self.healthy_nodes:
                self.healthy_nodes.remove(node_addr)
                logger.warning(f"Node {node_addr} appears to be down")

def get_healthy_nodes(self):
    with self.health_lock:  # Protect read too
        return list(self.healthy_nodes)
```

---

### Issue 5: Storage Lock Not Used Consistently (LOW PRIORITY)
**Location:** `storage.py`

**Problem:**
```python
async def store_message(self, message_id, message_json):
    async with self.storage_lock:  # Lock used here
        self.messages[message_id] = message_json
        await self.messages.wait_index()

async def get_message(self, message_id):
    # No lock used here - should be okay for reads but inconsistent
    message = await self.messages.get(message_id)
    return message
```

**Solution:**
Either: (a) Use locks consistently for all operations, or (b) Document why reads don't need locks (Raft handles this)

```python
async def get_message(self, message_id):
    """
    Retrieve a message by its ID
    Note: Read operations don't require lock as Raft ensures linearizability
    """
    try:
        message = await self.messages.get(message_id)
        return message
    except Exception as e:
        logger.error(f"Error retrieving message {message_id}: {e}")
        return None
```

---

### Issue 6: No Message Size Limit (MEDIUM PRIORITY)
**Location:** `server.py` and `server_cluster.py`

**Problem:**
```python
data = client_socket.recv(4096)  # Fixed buffer size
message = json.loads(data.decode('utf-8'))  # What if message > 4096 bytes?
```

Large messages might be truncated.

**Solution:**
```python
def handle_client(self, client_socket, address):
    username = None
    buffer = bytearray()
    
    try:
        while self.running:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            
            buffer.extend(chunk)
            
            # Try to parse complete JSON
            try:
                message_str = buffer.decode('utf-8')
                message = json.loads(message_str)
                buffer.clear()
                
                # Process message...
                self._process_client_message(message, client_socket, username)
                
            except json.JSONDecodeError:
                # Incomplete message - wait for more data
                if len(buffer) > 1048576:  # 1MB limit
                    logger.error("Message too large, dropping connection")
                    break
                continue
```

---

### Issue 7: NTP Offset Not Thread-Safe (LOW PRIORITY)
**Location:** `timesync.py`

**Problem:**
```python
def sync_time(self):
    with self.sync_lock:
        self.offset = response.offset  # Protected
        
def _periodic_sync(self):
    with self.sync_lock:
        self.offset = response.offset  # Protected
        
def get_synced_time(self):
    return time.time() + self.offset  # NOT protected!
```

**Solution:**
```python
def get_synced_time(self):
    with self.sync_lock:
        return time.time() + self.offset
```

OR (better performance):

```python
# Use atomic operations
import threading

def __init__(self):
    self._offset = 0
    self._offset_lock = threading.Lock()

def get_synced_time(self):
    # Read is atomic for simple types in Python (but let's be explicit)
    with self._offset_lock:
        offset = self._offset
    return time.time() + offset
```

---

### Issue 8: Server Doesn't Handle Client Socket Closure Gracefully
**Location:** `server_cluster.py`

**Problem:**
```python
data = client_socket.recv(4096)
if not data:
    break  # Exits loop, but what about broadcasts?
```

If a client disconnects while server is broadcasting, send fails.

**Solution:**
Already partially handled, but improve:

```python
def broadcast_message(self, message, exclude=None):
    with self.clients_lock:
        clients = list(self.clients.keys())
    
    data = json.dumps(message).encode('utf-8')
    failed_clients = []
    
    for client_socket in clients:
        if client_socket != exclude:
            try:
                client_socket.send(data)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                failed_clients.append(client_socket)
    
    # Clean up failed clients
    if failed_clients:
        with self.clients_lock:
            for client_socket in failed_clients:
                if client_socket in self.clients:
                    logger.info(f"Removing disconnected client: {self.clients[client_socket]}")
                    del self.clients[client_socket]
                try:
                    client_socket.close()
                except:
                    pass
```

---

## RECOMMENDED FIXES PRIORITY

### MUST FIX (Before Demo):
1. ✅ Issue 3: JSON parsing buffer (causes crashes)
2. ✅ Issue 1: Timeout inconsistency (causes reconnection loops)
3. ✅ Issue 4: Race condition in failover (causes crashes under load)

### SHOULD FIX (Before Submission):
4. ✅ Issue 2: Message queue overflow
5. ✅ Issue 6: Message size limit
6. ✅ Issue 8: Client cleanup in broadcast

### NICE TO FIX (If Time Permits):
7. ✅ Issue 5: Storage lock consistency (documentation is enough)
8. ✅ Issue 7: NTP offset thread safety

---

## TESTING EACH COMPONENT

See **TESTING_GUIDE.md** for comprehensive testing procedures.

### Quick Test Commands:

**Test 1: Start Everything**
```powershell
# Terminal 1-3: Servers
cd src
python server_cluster.py 0
python server_cluster.py 1
python server_cluster.py 2

# Terminal 4-5: Clients
cd src
python client.py
```

**Test 2: Fault Tolerance**
```powershell
# Kill server, watch client reconnect
# In server terminal, press Ctrl+C
```

**Test 3: Message Persistence**
```powershell
# Send messages, kill all servers, restart, check if messages preserved
```

**Test 4: Time Sync**
```powershell
# Check logs for "Time synchronized with" messages
# Verify timestamps on messages are consistent
```

**Test 5: Consensus**
```powershell
# Kill leader, watch new election
# Check logs for "Leader changed"
```

---

## HOW TO SPLIT FOR GITHUB (Step-by-Step)

### Step 1: Create Main Repository
```powershell
cd distributed-messaging-system
git init
git add .
git commit -m "Complete distributed messaging system"
git remote add origin https://github.com/yourusername/distributed-messaging-system.git
git push -u origin main
```

### Step 2: Each Member Creates Their Branch

**Member 1 (Fault Tolerance - IT23184558):**
```powershell
git checkout -b fault-tolerance-IT23184558
git rm -r src/consensus src/message_storage src/time_sync
git add src/failover/
git add src/client.py  # Keep reconnection logic
git commit -m "Member 1: Fault tolerance implementation"

# Add documentation
echo "# Fault Tolerance Implementation" > docs/member1_contribution.md
# Document your work in this file
git add docs/member1_contribution.md
git commit -m "Member 1: Add contribution documentation"

git push origin fault-tolerance-IT23184558
```

**Member 2 (Data Replication - IT23398184):**
```powershell
git checkout main
git checkout -b data-replication-IT23398184
git rm -r src/consensus src/failover src/time_sync
git add src/message_storage/
git commit -m "Member 2: Data replication and consistency"

# Add documentation
echo "# Data Replication Implementation" > docs/member2_contribution.md
git add docs/member2_contribution.md
git commit -m "Member 2: Add contribution documentation"

git push origin data-replication-IT23398184
```

**Member 3 (Time Sync - IT23294998 or IT23424432):**
```powershell
git checkout main
git checkout -b time-sync-IT23294998
git rm -r src/consensus src/failover src/message_storage
git add src/time_sync/
git commit -m "Member 3: Time synchronization implementation"

# Add documentation
echo "# Time Synchronization Implementation" > docs/member3_contribution.md
git add docs/member3_contribution.md
git commit -m "Member 3: Add contribution documentation"

git push origin time-sync-IT23294998
```

**Member 4 (Consensus - IT23424432):**
```powershell
git checkout main
git checkout -b consensus-IT23424432
git rm -r src/failover src/message_storage src/time_sync
git add src/consensus/
git commit -m "Member 4: Consensus and agreement implementation"

# Add documentation
echo "# Consensus Implementation" > docs/member4_contribution.md
git add docs/member4_contribution.md
git commit -m "Member 4: Add contribution documentation"

git push origin consensus-IT23424432
```

### Step 3: Create Individual READMEs

Each member should create a README in their branch explaining their contribution:

**Example: docs/member1_contribution.md**
```markdown
# Fault Tolerance Implementation
**Student:** D B Y BINUWARA  
**IT Number:** IT23184558  
**Component:** Fault Tolerance

## My Contributions

### 1. TCP-Based Health Checks
I implemented the health monitoring system using TCP socket connections...

[Code snippet]

### 2. Automatic Failover Detection
I developed the failover detection mechanism that...

[Code snippet]

### 3. Client Reconnection Logic
I created the automatic reconnection system...

[Code snippet]

## Testing Performed
- Test 1: Node failure detection
- Test 2: Client reconnection
- Test 3: Message queue preservation

## Challenges Faced
1. Timeout calibration
2. Race condition handling

## Results
- Detection time: 2-5 seconds
- Reconnection success rate: 100%
```

### Step 4: Create Pull Requests

Each member creates a pull request from their branch to main, describing their work.

---

## ALTERNATIVE: Separate Repos Per Member

If you want completely separate repositories:

```powershell
# Member 1
mkdir fault-tolerance-component
cd fault-tolerance-component
# Copy only src/failover/ and related files
git init
git add .
git commit -m "Fault tolerance component"
git remote add origin https://github.com/member1/fault-tolerance-component.git
git push -u origin main
```

Repeat for each member with their respective components.

---

## SUBMISSION PACKAGE STRUCTURE

```
distributed-messaging-system/
├── README.md (Main project overview)
├── TESTING_GUIDE.md (Testing procedures)
├── LOGIC_ISSUES.md (This file)
├── github_links.txt (Links to all repos/branches)
├── report.pdf (10-12 page report)
├── presentation.pptx (Presentation slides)
├── youtube_link.txt (Presentation video link)
└── src/ (Complete source code)
```

**github_links.txt format:**
```
Main Repository: https://github.com/username/distributed-messaging-system

Member Contributions:
- IT23184558 (Fault Tolerance): https://github.com/username/repo/tree/fault-tolerance-IT23184558
- IT23398184 (Data Replication): https://github.com/username/repo/tree/data-replication-IT23398184
- IT23294998 (Time Sync): https://github.com/username/repo/tree/time-sync-IT23294998
- IT23424432 (Consensus): https://github.com/username/repo/tree/consensus-IT23424432
```

---

## SUMMARY

**Logic Issues Found:** 8 (3 high priority, 3 medium, 2 low)  
**Testing Strategy:** Component-by-component + integration testing  
**GitHub Strategy:** Branch-based with individual documentation  
**Names/IT Numbers Source:** Instruct.txt file (verify accuracy!)

**Next Steps:**
1. Fix high-priority issues (1, 3, 4)
2. Test each component thoroughly
3. Create branches and document individual contributions
4. Record presentation showing all components working
5. Write report explaining design decisions and trade-offs

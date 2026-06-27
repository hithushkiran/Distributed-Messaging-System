"""
Quick Fixes for Critical Logic Issues
Apply these fixes before testing/demo
"""

# =============================================================================
# FIX 1: Client JSON Parsing Buffer Issue (HIGH PRIORITY)
# File: src/client.py
# =============================================================================

# REPLACE the receive_messages method with this improved version:

"""
def receive_messages(self):
    '''Handle receiving messages from the server with proper JSON parsing'''
    buffer = bytearray()
    
    while self.running:
        if not self.connected:
            time.sleep(1)
            continue
        
        try:
            # Set socket to non-blocking read with timeout
            self.client_socket.settimeout(0.5)
            
            # Receive data
            chunk = self.client_socket.recv(4096)
            if not chunk:
                logger.info("Lost connection to server")
                self.connected = False
                self.reconnect()
                buffer.clear()  # Clear buffer on disconnect
                continue
            
            # Add to buffer
            buffer.extend(chunk)
            
            # Try to parse complete JSON messages
            while buffer:
                try:
                    # Decode buffer
                    message_str = buffer.decode('utf-8')
                    
                    # Try to parse a complete JSON object
                    decoder = json.JSONDecoder()
                    message, idx = decoder.raw_decode(message_str)
                    
                    # Successfully parsed - process message
                    self._process_received_message(message)
                    
                    # Remove processed portion from buffer
                    buffer = buffer[idx:].lstrip()
                    
                except json.JSONDecodeError:
                    # Incomplete JSON - wait for more data
                    if len(buffer) > 1048576:  # 1MB safety limit
                        logger.error("Buffer too large, clearing")
                        buffer.clear()
                    break
                except UnicodeDecodeError:
                    # Invalid UTF-8 data, clear buffer
                    logger.warning("Received invalid UTF-8 data")
                    buffer.clear()
                    break
        
        except socket.timeout:
            # This is expected - just continue the loop
            pass
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            self.connected = False
            self.reconnect()
            buffer.clear()

def _process_received_message(self, message):
    '''Process a parsed message'''
    try:
        if message.get("type") == "chat":
            sender = message.get('sender', 'Unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', time.time())
            
            # Format timestamp
            time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            print(f"\\n[{time_str}] {sender}: {content}")
        
        elif message.get("type") == "system":
            content = message.get('content', '')
            timestamp = message.get('timestamp', time.time())
            
            # Format timestamp
            time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            print(f"\\n[{time_str}] SYSTEM: {content}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
"""

# =============================================================================
# FIX 2: Message Queue Overflow Protection (MEDIUM PRIORITY)
# File: src/client.py
# =============================================================================

# REPLACE the send_message method with this version:

"""
def send_message(self, message_type, content):
    '''
    Send a formatted message to the server
    
    Args:
        message_type (str): Type of message (e.g., 'chat', 'login', 'logout')
        content (str): Message content
        
    Returns:
        bool: True if message sent successfully, False otherwise
    '''
    if not self.connected:
        logger.warning("Not connected to any server")
        with self.message_lock:
            # Limit queue size to prevent memory issues
            MAX_QUEUE_SIZE = 100
            if len(self.message_queue) < MAX_QUEUE_SIZE:
                self.message_queue.append((message_type, content))
            else:
                logger.warning(f"Message queue full ({MAX_QUEUE_SIZE}), dropping oldest message")
                self.message_queue.pop(0)  # Remove oldest
                self.message_queue.append((message_type, content))
        return False
    
    try:
        message = {
            "type": message_type,
            "sender": self.username,
            "content": content,
            "timestamp": time.time()
        }
        
        data = json.dumps(message).encode('utf-8')
        self.client_socket.send(data)
        return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        self.connected = False
        
        # Queue the message for resending after reconnection
        with self.message_lock:
            MAX_QUEUE_SIZE = 100
            if len(self.message_queue) < MAX_QUEUE_SIZE:
                self.message_queue.append((message_type, content))
            else:
                self.message_queue.pop(0)
                self.message_queue.append((message_type, content))
        
        return False
"""

# =============================================================================
# FIX 3: Failover Health Check Race Condition (HIGH PRIORITY)
# File: src/failover/failover.py
# =============================================================================

# ADD to __init__ method:

"""
def __init__(self, cluster_nodes):
    self.cluster_nodes = cluster_nodes
    self.current_leader = None
    self.healthy_nodes = set(cluster_nodes)
    self.health_lock = threading.Lock()  # ADD THIS LINE
    self.stop_event = threading.Event()
    self.monitor_thread = None
    self.health_check_interval = 3
    
    logger.info(f"Failover handler initialized with {len(cluster_nodes)} nodes")
"""

# REPLACE _check_node_health method:

"""
def _check_node_health(self):
    '''Check the health of all cluster nodes'''
    for node_addr in self.cluster_nodes:
        healthy = self._is_node_alive(node_addr)
        
        # Thread-safe health status updates
        with self.health_lock:
            if healthy and node_addr not in self.healthy_nodes:
                # Node has recovered
                self.healthy_nodes.add(node_addr)
                logger.info(f"Node {node_addr} is now healthy")
            elif not healthy and node_addr in self.healthy_nodes:
                # Node has failed
                self.healthy_nodes.remove(node_addr)
                logger.warning(f"Node {node_addr} appears to be down")
"""

# REPLACE get_healthy_nodes method:

"""
def get_healthy_nodes(self):
    '''
    Get a list of currently healthy nodes
    
    Returns:
        list: List of healthy node addresses
    '''
    with self.health_lock:  # Thread-safe read
        return list(self.healthy_nodes)
"""

# =============================================================================
# FIX 4: Timeout Alignment (HIGH PRIORITY)
# File: src/failover/failover.py
# =============================================================================

# OPTION 1: Increase health check timeout to match client
"""
def _is_node_alive(self, node_addr):
    try:
        host, port = node_addr.split(':')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # CHANGED FROM 2 to 5 - matches client timeout
            s.connect((host, int(port)))
            return True
    except Exception:
        return False
"""

# OPTION 2: Add consecutive failure requirement (RECOMMENDED)
"""
def __init__(self, cluster_nodes):
    self.cluster_nodes = cluster_nodes
    self.current_leader = None
    self.healthy_nodes = set(cluster_nodes)
    self.health_lock = threading.Lock()
    self.failed_checks = {}  # ADD THIS - track consecutive failures
    self.stop_event = threading.Event()
    self.monitor_thread = None
    self.health_check_interval = 3
    
    logger.info(f"Failover handler initialized with {len(cluster_nodes)} nodes")

def _check_node_health(self):
    '''Check the health of all cluster nodes with grace period'''
    for node_addr in self.cluster_nodes:
        healthy = self._is_node_alive(node_addr)
        
        with self.health_lock:
            if not healthy:
                # Track consecutive failures
                self.failed_checks[node_addr] = self.failed_checks.get(node_addr, 0) + 1
                
                # Only mark as unhealthy after 2 consecutive failures
                if self.failed_checks[node_addr] >= 2 and node_addr in self.healthy_nodes:
                    self.healthy_nodes.remove(node_addr)
                    logger.warning(f"Node {node_addr} failed {self.failed_checks[node_addr]} health checks - marked as down")
            else:
                # Reset failure counter on successful check
                if node_addr in self.failed_checks:
                    del self.failed_checks[node_addr]
                
                # Add to healthy nodes if not already there
                if node_addr not in self.healthy_nodes:
                    self.healthy_nodes.add(node_addr)
                    logger.info(f"Node {node_addr} is now healthy")
"""

# =============================================================================
# FIX 5: Server Message Buffer Handling (MEDIUM PRIORITY)
# File: src/server_cluster.py
# =============================================================================

# REPLACE handle_client method with buffered version:

"""
def handle_client(self, client_socket, address):
    '''Handle communication with a connected client'''
    username = None
    buffer = bytearray()
    
    try:
        while self.running:
            # Receive data from client
            data = client_socket.recv(4096)
            if not data:
                # Client disconnected
                break
            
            # Add to buffer
            buffer.extend(data)
            
            # Process complete messages
            while buffer:
                try:
                    # Try to decode and parse JSON
                    message_str = buffer.decode('utf-8')
                    decoder = json.JSONDecoder()
                    message, idx = decoder.raw_decode(message_str)
                    
                    # Successfully parsed - remove from buffer
                    buffer = buffer[idx:].lstrip()
                    
                    # Process the message
                    message_type = message.get("type")
                    
                    if message_type == "login":
                        username = message.get("sender")
                        # Register client
                        with self.clients_lock:
                            self.clients[client_socket] = username
                        
                        timestamp = self.time_sync.get_synced_time()
                        
                        # Send welcome message to client
                        self.send_system_message(client_socket, f"Welcome, {username}!")
                        
                        # Broadcast join message
                        self.broadcast_message({
                            "type": "system",
                            "content": f"{username} has joined the chat",
                            "timestamp": timestamp
                        }, exclude=client_socket)
                        
                        # Store in persistent storage
                        self._store_message_async("join", username, f"{username} joined", timestamp)
                    
                    elif message_type == "chat":
                        if username:
                            content = message.get("content", "")
                            timestamp = self.time_sync.get_synced_time()
                            
                            # Broadcast the message
                            self.broadcast_message({
                                "type": "chat",
                                "sender": username,
                                "content": content,
                                "timestamp": timestamp
                            })
                            
                            # Store in persistent storage
                            self._store_message_async("chat", username, content, timestamp)
                    
                    elif message_type == "logout":
                        break
                
                except json.JSONDecodeError:
                    # Incomplete JSON - wait for more data
                    if len(buffer) > 1048576:  # 1MB limit
                        logger.error(f"Buffer overflow for client {address}")
                        break
                    break  # Exit inner loop, wait for more data
                except UnicodeDecodeError:
                    logger.warning(f"Invalid UTF-8 from {address}")
                    buffer.clear()
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    break
    
    finally:
        # Clean up when client disconnects
        if username:
            with self.clients_lock:
                if client_socket in self.clients:
                    del self.clients[client_socket]
            
            timestamp = self.time_sync.get_synced_time()
            
            # Broadcast leave message
            self.broadcast_message({
                "type": "system",
                "content": f"{username} has left the chat",
                "timestamp": timestamp
            })
            
            # Store in persistent storage
            self._store_message_async("leave", username, f"{username} left", timestamp)
        
        try:
            client_socket.close()
        except:
            pass
        
        logger.info(f"Connection closed for {address}")
"""

# =============================================================================
# FIX 6: Improved Broadcast Error Handling (MEDIUM PRIORITY)
# File: src/server_cluster.py
# =============================================================================

# REPLACE broadcast_message method:

"""
def broadcast_message(self, message, exclude=None):
    '''Broadcast a message to all connected clients with error handling'''
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
                    username = self.clients[client_socket]
                    logger.info(f"Removing disconnected client: {username}")
                    del self.clients[client_socket]
                try:
                    client_socket.close()
                except:
                    pass
"""

# =============================================================================
# TESTING AFTER FIXES
# =============================================================================

"""
After applying these fixes, test:

1. Start 3 servers
2. Start 2 clients
3. Send messages rapidly (test buffer handling)
4. Kill one server (test failover)
5. Kill client connection (test cleanup)
6. Send 150 messages while disconnected (test queue limit)
7. Reconnect (test message delivery)

Expected behavior:
- No JSON parsing errors
- Clean failover (2-5 seconds)
- No race condition crashes
- Message queue stays under 100
- Clean client disconnection
"""

print("Apply these fixes to resolve critical logic issues")
print("See LOGIC_ISSUES_AND_SOLUTIONS.md for detailed explanations")

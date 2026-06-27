# 💬 Client Usage Guide
## How to Send Messages in Your Distributed System

---

## 🎯 Quick Start

### Start the Interactive Client

```powershell
python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002
```

### What Happens:

1. **Client connects** to one of the servers
2. **Prompts for username**: `Enter your username:`
3. **Enter username**: Type any name (e.g., "Alice") and press Enter
4. **Start chatting**: Type messages and press Enter to send
5. **Messages replicate** automatically to all nodes

---

## 📝 Example Session

```
PS> python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002

Connected to server 127.0.0.1:5000
Enter your username: Alice
Welcome Alice! Connected to server 127.0.0.1:5000
Type your messages (Ctrl+C to exit)

> Hello from distributed system!
[Sent]

> Testing message replication
[Sent]

> Raft consensus working perfectly!
[Sent]

> (Press Ctrl+C to exit)

Disconnecting...
Client stopped
```

---

## 🔍 What the Client Does

### Connection Process:

1. **Tries each server** in the cluster list
2. **Connects to first available** server
3. **Automatically reconnects** if disconnected
4. **Finds the leader** (servers tell client who the leader is)

### Message Sending:

1. **User types message** and presses Enter
2. **Client sends to connected server**
3. **If server is follower**, it redirects to leader
4. **Leader replicates** to all followers
5. **Client receives confirmation**

---

## 🎭 Behind the Scenes

### What Happens on the Server Side:

**When message arrives at LEADER:**
```
[Leader Terminal]
- Received message from Alice: "Hello from distributed system!"
- Storing message with ID: msg_1728234605_001
- Replicating to follower 127.0.0.1:5001... ✓
- Replicating to follower 127.0.0.1:5002... ✓
- Message committed successfully
```

**On FOLLOWER terminals:**
```
[Follower 1 Terminal]
- Received replicated message: msg_1728234605_001
- Stored message from Alice

[Follower 2 Terminal]
- Received replicated message: msg_1728234605_001
- Stored message from Alice
```

### If Client Connects to Follower:

```
Client → Follower (port 5001)
           ↓
    "I'm not the leader!"
           ↓
    "Leader is at 127.0.0.1:5000"
           ↓
Client → Leader (port 5000)
           ↓
    Message processed
```

---

## 🚀 Alternative: Using curl for Testing

If you want to send single messages without interactive mode, use curl:

```powershell
# Send message to specific server
curl -X POST http://localhost:5000/send ^
  -H "Content-Type: application/json" ^
  -d "{\"sender\": \"Alice\", \"content\": \"Hello World\"}"

# Query messages
curl http://localhost:5000/messages

# Check cluster status
curl http://localhost:5000/status
```

---

## 🎯 For Your Demo

### Recommended Approach:

**Use interactive client because it:**
- ✅ Shows **real user experience**
- ✅ More **engaging** for audience
- ✅ **Live typing** demonstrates real-time replication
- ✅ Easier to explain to non-technical audience

### Demo Steps:

1. **Start client** in Terminal 5
2. **Type username** (e.g., "Alice")
3. **Type 3-5 messages** one by one
4. **Point to server terminals** showing replication
5. **Keep client running** while you verify with curl
6. **Later** (optional): Start second client as different user

---

## 💡 Pro Tips

### Multiple Clients:

You can run multiple clients simultaneously:

```powershell
# Terminal 5 - Client 1 (Alice)
python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002

# Terminal 6 - Client 2 (Bob)
python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002
```

All clients see all messages in real-time!

### What to Say During Demo:

**When starting client:**
> "The client connects to any available server in our cluster."

**When typing username:**
> "Each user identifies themselves with a username."

**When sending first message:**
> "Watch the server terminals - the leader receives this message and immediately replicates it to all followers."

**After sending messages:**
> "All messages are now stored on all 3 nodes with strong consistency. Let's verify..."

---

## 🐛 Troubleshooting

### Client Can't Connect:

```
Unable to connect to server 127.0.0.1:5000: [Errno 10061]
```

**Solution:** Make sure at least one server is running!

```powershell
# Check if servers are running
netstat -an | findstr "5000 5001 5002"

# Start servers if needed
python src/server_cluster.py 0
python src/server_cluster.py 1
python src/server_cluster.py 2
```

### Client Connects but Messages Don't Send:

**Possible causes:**
1. Connected to follower, but follower can't reach leader
2. Network issue between nodes
3. Leader not elected yet

**Solution:** 
- Check server terminals for leader election messages
- Wait 10 seconds for election to complete
- Restart client

---

## 📊 Message Format

Messages are stored as JSON:

```json
{
  "id": "msg_1728234605_001",
  "sender": "Alice",
  "content": "Hello from distributed system!",
  "timestamp": "2025-10-06 19:30:05",
  "term": 1
}
```

**Fields:**
- `id`: Unique message identifier (timestamp + sequence)
- `sender`: Username who sent the message
- `content`: The actual message text
- `timestamp`: When message was created (synchronized time)
- `term`: Raft term when message was stored

---

## 🎬 Demo Script Integration

**In your demo, when you reach Part 3:**

1. Open Terminal 5
2. Run: `python src/client.py --servers 127.0.0.1:5000,127.0.0.1:5001,127.0.0.1:5002`
3. Type username: `Alice`
4. Send messages one by one:
   - `Hello from distributed system!`
   - `Testing message replication`
   - `Raft consensus working perfectly!`
5. **Keep terminal open** (don't close client)
6. Use curl in same or another terminal for verification

**This shows:**
- ✅ Real user experience
- ✅ Live replication
- ✅ Interactive system
- ✅ Professional demonstration

---

**Key Takeaway:** The client is interactive (like a chat application) rather than command-line based. This makes your demo more engaging and easier to understand for the audience! 💪

"""
Simple HTTP API server to query cluster status and messages
Runs alongside the main socket server on port +100 (e.g., 5100, 5101, 5102)
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

logger = logging.getLogger("HTTPQueryAPI")


class QueryHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for status and messages"""
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == "/messages":
                self.handle_messages()
            elif self.path == "/status":
                self.handle_status()
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, str(e))
    
    def handle_messages(self):
        """Return all messages"""
        try:
            # Get message storage from server
            storage = self.server.cluster_server.message_storage
            
            # Get all messages synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            messages_data = loop.run_until_complete(storage.get_all_messages())
            loop.close()
            
            # Parse messages
            messages = []
            for msg_id, msg_json in messages_data:
                try:
                    msg = json.loads(msg_json)
                    messages.append({
                        "message_id": msg_id,
                        "content": msg.get("content", ""),
                        "sender": msg.get("sender", ""),
                        "timestamp": msg.get("timestamp", 0)
                    })
                except:
                    pass
            
            # Sort by timestamp
            messages.sort(key=lambda x: x["timestamp"])
            
            response = {
                "count": len(messages),
                "messages": messages
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            self.send_error(500, str(e))
    
    def handle_status(self):
        """Return cluster status as strict JSON for PowerShell compatibility"""
        try:
            self.protocol_version = "HTTP/1.1"  # Ensure HTTP/1.1 for PowerShell compatibility
            server = self.server.cluster_server
            consensus = server.consensus
            failover = server.failover

            # Get state safely from raft_node (consensus wraps raft_node)
            state_value = "UNKNOWN"
            term_value = 0
            leader_value = None
            
            if consensus.raft_node is not None:
                raft = consensus.raft_node
                if hasattr(raft, 'state') and raft.state is not None:
                    state_value = raft.state.name  # FOLLOWER, LEADER, or CANDIDATE
                if hasattr(raft, 'current_term'):
                    term_value = int(raft.current_term)
                if hasattr(raft, 'current_leader') and raft.current_leader:
                    leader_value = str(raft.current_leader)

            # Build a strictly serializable response
            response = {
                "node_id": str(server.node_addr),
                "state": state_value,
                "term": term_value,
                "leader": leader_value,
                "healthy_nodes": [str(n) for n in getattr(failover, 'healthy_nodes', [])]
            }

            json_bytes = (json.dumps(response, indent=2) + "\n").encode("utf-8")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(json_bytes)))
            self.end_headers()
            self.wfile.write(json_bytes)
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            self.send_error(500, str(e))


def start_http_api(cluster_server, http_port):
    """Start HTTP API server in background thread"""
    try:
        httpd = HTTPServer(('127.0.0.1', http_port), QueryHandler)
        httpd.cluster_server = cluster_server
        
        def run_server():
            logger.info(f"HTTP Query API started on port {http_port}")
            httpd.serve_forever()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        return httpd
    except Exception as e:
        logger.error(f"Failed to start HTTP API: {e}")
        return None

"""
Simple query script to check messages and status via socket connection
Used for demo purposes to verify replication
"""
import socket
import json
import sys

def query_server(host, port, query_type):
    """Query server for messages or status"""
    try:
        # Connect to server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((host, port))
        
        # Send query request
        request = {
            "type": "query",
            "query_type": query_type  # "messages" or "status"
        }
        client_socket.send(json.dumps(request).encode('utf-8'))
        
        # Receive response
        response = client_socket.recv(4096).decode('utf-8')
        client_socket.close()
        
        # Parse and pretty print
        data = json.loads(response)
        print(json.dumps(data, indent=2))
        
    except socket.timeout:
        print(f"Error: Connection to {host}:{port} timed out")
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"Error: Connection to {host}:{port} refused (server not running?)")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response: {e}")
        print(f"Raw response: {response}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python query_server.py <port> <messages|status>")
        print("Example: python query_server.py 5000 messages")
        sys.exit(1)
    
    port = int(sys.argv[1])
    query_type = sys.argv[2]
    
    if query_type not in ["messages", "status"]:
        print("Error: query_type must be 'messages' or 'status'")
        sys.exit(1)
    
    query_server("127.0.0.1", port, query_type)

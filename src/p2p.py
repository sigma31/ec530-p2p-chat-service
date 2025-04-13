import socket
import threading
import signal
import sys
import os

DISCOVERY_SERVER = ("127.0.0.1", 5000) # Hard coded for now
peers = {}

def register_with_discovery(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(DISCOVERY_SERVER)
        sock.send(f"REGISTER {socket.gethostbyname(socket.gethostname())} {port}".encode('utf-8'))
        sock.close()
    except Exception as e:
        print(f"Failed to register with discovery server: {e}")

def fetch_peer_list():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(DISCOVERY_SERVER)
        sock.send("GET_PEERS".encode('utf-8'))
        response = sock.recv(4096).decode('utf-8')
        sock.close()

        peer_list = []
        for peer in response.split("\n"):
            if peer.strip():
                host, port = peer.split(":")
                peer_list.append((host, int(port)))  # Ensure port is an integer
        return peer_list

    except Exception as e:
        print(f"Failed to fetch peer list: {e}")
        return []

def unregister_from_discovery(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(DISCOVERY_SERVER)
        sock.send(f"UNREGISTER {socket.gethostbyname(socket.gethostname())} {port}".encode('utf-8'))
        sock.close()
    except Exception as e:
        print(f"Failed to unregister from discovery server: {e}")

def start_peer_server(peers, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print(f"[PEER SERVER STARTED] Listening on port {port}...")

    def handle_peer(peer_socket):
        while True:
            try:
                message = peer_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                print(f"[PEER] {message}")
            except:
                break
        peer_socket.close()

    while True:
        peer_socket, _ = server.accept()
        threading.Thread(target=handle_peer, args=(peer_socket,)).start()

def fetch_single_peer(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(DISCOVERY_SERVER)
        sock.send(f"CONNECT_TO {host} {port}".encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')
        sock.close()

        if not response or response == "NOT_FOUND":
            print(f"No peer found with host: {host} and port: {port}")
            return None
        
        parts = response.split(":")
        if len(parts) != 2:
            print(f"Invalid response from discovery server: {response}")
            return None

        peer_host, peer_port = parts
        return (peer_host, int(peer_port)) 

    except Exception as e:
        print(f"Failed to fetch peer {host}:{port}: {e}")
        return None

        
def list_peers():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(DISCOVERY_SERVER)
        sock.send("LIST_PEERS".encode('utf-8'))
        response = sock.recv(4096).decode('utf-8')
        sock.close()

        if response == "NO_PEERS":
            print("No peers available.")
        else:
            print("\nAvailable Peers:")
            print(response)
    except Exception as e:
        print(f"Failed to list peers: {e}")
        
def broadcast(message, peer_sockets):
    for peer_socket in peer_sockets:
        try:
            peer_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")

def receive_messages(peer_socket):
    while True:
        try:
            message = peer_socket.recv(1024).decode('utf-8')
            if message:
                print(f"\n[Message Received] {message}")
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def connect_to_peers(peer_list):
    if not peer_list:
        print("No peers available to connect.")
        return

    for peer_info in peer_list:
        try:
            host, port = peer_info
            if (host, port) in peers:
                print(f"[INFO] Already connected to {host}:{port}")
                continue

            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((host, port))
            peers[(host, port)] = peer
            threading.Thread(target=receive_messages, args=(peer,), daemon=True).start()
            print(f"[CONNECTED TO PEER] {host}:{port}")

        except Exception as e:
            print(f"Failed to connect to peer {host}:{port}: {e}")
            
def graceful_exit(port):
    print("\n[DISCONNECTING] Unregistering from discovery server and closing connections...")
    unregister_from_discovery(port)
    for peer_sock in peers.values():
        try:
            peer_sock.close()
        except:
            pass
    print("[SHUTDOWN COMPLETE] Peer disconnected.")
    sys.exit(0)

def start_peer(port):
    register_with_discovery(port)
    signal.signal(signal.SIGINT, lambda sig, frame: graceful_exit(port))
    signal.signal(signal.SIGTERM, lambda sig, frame: graceful_exit(port))

    threading.Thread(target=start_peer_server, args=(peers, port), daemon=True).start()

    while True:
        choice = input("\nOptions:\n1. List all peers\n2. Connect to a peer\n3. Connect to all peers\n4. Send a message to all peers\n5. Send a message to one peer\n6. Disconnect\nEnter choice: ").strip()

        if choice == "1":
            list_peers()
            
        elif choice == "2":
            target_host = input("Enter the peer host to connect to: ").strip()
            target_port = input("Enter the peer port: ").strip()
            if not target_port.isdigit():
                print("Invalid port number.")
                continue

            single_peer = fetch_single_peer(target_host, int(target_port))
            if single_peer:
                connect_to_peers([single_peer])
            else:
                print(f"Peer {target_host}:{target_port} not found.")

        elif choice == "3":
            available_peers = fetch_peer_list()
            connect_to_peers(available_peers)

        elif choice == "4":
            if not peers:
                print("No active connections. Use option 2 or 3 to connect first.")
            else:
                message = input("Enter message: ")
                broadcast(message, peers.values())

        elif choice == "5":
            if not peers:
                print("No active connections.")
            else:
                print("Connected peers:")
                for idx, ((host, port), _) in enumerate(peers.items(), 1):
                    print(f"{idx}. {host}:{port}")

                selection = input("Select peer by number: ")
                if not selection.isdigit() or int(selection) < 1 or int(selection) > len(peers):
                    print("Invalid selection.")
                    continue

                selected_peer = list(peers.items())[int(selection) - 1]
                _, peer_socket = selected_peer
                message = input("Enter message to send: ")
                try:
                    peer_socket.send(message.encode('utf-8'))
                except Exception as e:
                    print(f"Failed to send message: {e}")

        elif choice == "6":
            graceful_exit(port)

if __name__ == "__main__":
    port_env = os.environ.get("PEER_PORT")
    if port_env and port_env.isdigit():
        port = int(port_env)
    else:
        port = int(input("Enter your listening port: "))

    start_peer(port)

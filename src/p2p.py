import socket
import threading

DISCOVERY_SERVER = ("127.0.0.1", 5000) # Hard coded for now
peers = []

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

def fetch_single_peer(host):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(DISCOVERY_SERVER)
        sock.send(f"CONNECT_TO {host}".encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')
        sock.close()

        if not response or response == "NOT_FOUND":
            print(f"No peer found with host: {host}")
            return None
        
        parts = response.split(":")
        if len(parts) != 2:
            print(f"Invalid response from discovery server: {response}")
            return None

        peer_host, peer_port = parts
        return (peer_host, int(peer_port)) 

    except Exception as e:
        print(f"Failed to fetch peer {host}: {e}")
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
        
def broadcast(message, peers):
    for peer in peers:
        try:
            peer.send(message.encode('utf-8'))  
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
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((host, port))
            peers.append(peer) 
            threading.Thread(target=receive_messages, args=(peer,)).start()
            print(f"[CONNECTED TO PEER] {host}:{port}")

            while True:
                message = input("Enter message to send (or type 'exit' to stop): ")
                if message.lower() == "exit":
                    break
                peer.send(message.encode('utf-8'))  

        except Exception as e:
            print(f"Failed to connect to peer {host}:{port}: {e}")

def start_peer(port):
    global peers
    peers = []

    register_with_discovery(port)
    threading.Thread(target=start_peer_server, args=(peers, port)).start()

    while True:
        choice = input("\nOptions:\n1. List all peers\n2. Connect to a peer\n3. Connect to all peers\n4. Send a message\nEnter choice: ").strip()

        if choice == "1":
            list_peers()
        elif choice == "2":
            target_host = input("Enter the peer host to connect to (only IP, without port): ").strip()
            single_peer = fetch_single_peer(target_host)
            if single_peer:
                connect_to_peers([single_peer])
            else:
                print(f"Peer {target_host} not found.")
        elif choice == "3":
            available_peers = fetch_peer_list()
            connect_to_peers(available_peers)
        elif choice == "4":
            if not peers:
                print("No active connections. Use option 2 or 3 to connect first.")
            else:
                message = input("Enter message: ")
                broadcast(message, peers)
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    port = int(input("Enter your listening port: "))
    start_peer(port)
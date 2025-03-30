import socket
import threading

DISCOVERY_SERVER = ("127.0.0.1", 5000)  # Replace with actual discovery server IP/host
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

def connect_to_peers(peer_list):
    global peers

    for host, port in peer_list:
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((host, int(port)))
            peers.append(peer_socket)  
            print(f"[CONNECTED TO PEER] {host}:{port}")
        except Exception as e:
            print(f"Failed to connect to {host}:{port}: {e}")

def start_peer(port):
    global peers
    peers = []  # Reset peer list

    register_with_discovery(port)
    threading.Thread(target=start_peer_server, args=(peers, port)).start()

    available_peers = fetch_peer_list() 
    connect_to_peers(available_peers)  

    print("[PEER READY] Type messages to broadcast:")

    try:
        while True:
            message = input()
            for peer in peers: 
                try:
                    peer.send(message.encode('utf-8'))
                except:
                    peers.remove(peer)
    except KeyboardInterrupt:
        print("\n[EXITING] Unregistering...")
        unregister_from_discovery(port)

if __name__ == "__main__":
    port = int(input("Enter your listening port: "))
    start_peer(port)

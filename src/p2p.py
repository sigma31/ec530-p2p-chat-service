import socket
import threading

# Peer to Peer code
def handle_peer(peer_socket, peer_address, peers):
    print(f"[NEW CONNECTION] {peer_address} connected.")
    peers.append(peer_socket)

    try:
        while True:
            message = peer_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"[{peer_address}] {message}")
            broadcast(message, peer_socket, peers)
    except ConnectionResetError:
        print(f"[DISCONNECT] {peer_address} disconnected.")
    finally:
        peers.remove(peer_socket)
        peer_socket.close()

def broadcast(message, sender_socket, peers):
    for peer in peers:
        if peer != sender_socket:
            try:
                peer.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message: {e}")

def start_peer_server(peers, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print(f"[PEER SERVER STARTED] Listening on port {port}...")

    while True:
        peer_socket, peer_address = server.accept()
        peer_thread = threading.Thread(target=handle_peer, args=(peer_socket, peer_address, peers))
        peer_thread.start()

def connect_to_peer(host, port, peers):
    try:
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.connect((host, port))
        peers.append(peer)
        threading.Thread(target=receive_messages, args=(peer,)).start()
        print(f"[CONNECTED TO PEER] {host}:{port}")
    except Exception as e:
        print(f"Failed to connect to peer: {e}")

def receive_messages(peer_socket):
    while True:
        try:
            message = peer_socket.recv(1024).decode('utf-8')
            print(message)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def start_peer(port, initial_peer=None):
    peers = []
    threading.Thread(target=start_peer_server, args=(peers, port)).start()

    if initial_peer:
        host, peer_port = initial_peer.split(':')
        connect_to_peer(host, int(peer_port), peers)

    print(f"[PEER READY] Listening on port {port}. Connect using other peers.")

    while True:
        message = input()
        broadcast(message, None, peers)

if __name__ == "__main__":
    port = int(input("Enter your listening port: "))
    initial_peer = input("Enter initial peer (host:port) or press Enter to skip: ").strip()
    start_peer(port, initial_peer if initial_peer else None)
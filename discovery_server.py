import socket
import threading

peers = set()  # Store active peers as (host, port) tuples
peers_lock = threading.Lock()

def handle_client(client_socket, client_address):
    try:
        data = client_socket.recv(1024).decode('utf-8')
        if not data:
            return

        command, *args = data.strip().split()

        if command == "REGISTER":
            if len(args) != 2:
                client_socket.send("INVALID_COMMAND".encode('utf-8'))
                return

            host, port = args
            peer = (host, int(port))
            with peers_lock:
                if peer not in peers:
                    peers.add(peer)
                    print(f"[REGISTERED] {peer}")
            client_socket.send("OK".encode('utf-8'))

        elif command == "GET_PEERS":
            with peers_lock:
                peer_list = "\n".join(f"{h}:{p}" for h, p in peers)
            client_socket.send(peer_list.encode('utf-8'))

        elif command == "LIST_PEERS":
            with peers_lock:
                if peers:
                    peer_list = "\n".join(f"{h}:{p}" for h, p in peers)
                    client_socket.send(peer_list.encode('utf-8'))
                else:
                    client_socket.send("NO_PEERS".encode('utf-8'))

        elif command == "CONNECT_TO":
            if len(args) == 2:
                requested_host = args[0]
                requested_port = int(args[1])
                with peers_lock:
                    if (requested_host, requested_port) in peers:
                        client_socket.send(f"{requested_host}:{requested_port}".encode('utf-8'))
                    else:
                        client_socket.send("NOT_FOUND".encode('utf-8'))
            else:
                client_socket.send("INVALID_COMMAND".encode('utf-8'))

        elif command == "UNREGISTER":
            if len(args) != 2:
                client_socket.send("INVALID_COMMAND".encode('utf-8'))
                return

            host, port = args
            peer = (host, int(port))
            with peers_lock:
                if peer in peers:
                    peers.remove(peer)
                    print(f"[UNREGISTERED] {peer}")
            client_socket.send("OK".encode('utf-8'))

        else:
            client_socket.send("UNKNOWN_COMMAND".encode('utf-8'))

    except (ConnectionResetError, BrokenPipeError):
        print(f"[DISCONNECTED] Client {client_address} disconnected unexpectedly.")
        remove_peer(client_address)

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        client_socket.close()

def remove_peer(client_address):
    """ Removes the peer from the known peer list if it disconnects unexpectedly. """
    with peers_lock:
        disconnected_peers = [peer for peer in peers if peer[0] == client_address[0]]
        for peer in disconnected_peers:
            peers.remove(peer)
            print(f"[CLEANUP] Removed peer {peer} due to disconnection.")

def start_discovery_server(port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen(10)
    print(f"[DISCOVERY SERVER] Running on port {port}")

    while True:
        client_socket, client_address = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True).start()

if __name__ == "__main__":
    start_discovery_server(5000)

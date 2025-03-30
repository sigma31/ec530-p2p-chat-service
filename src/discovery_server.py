import socket
import threading

peers = set()  # Store active peers as (host, port) tuples

def handle_client(client_socket):
    try:
        data = client_socket.recv(1024).decode('utf-8')
        command, *args = data.split()

        if command == "REGISTER":
            host, port = args
            peer = (host, int(port))
            if peer not in peers:
                peers.add(peer)
                print(f"[REGISTERED] {peer}")
            client_socket.send("OK".encode('utf-8'))

        elif command == "GET_PEERS":
            client_socket.send("\n".join(f"{h}:{p}" for h, p in peers).encode('utf-8'))

        elif command == "UNREGISTER":
            host, port = args
            peer = (host, int(port))
            if peer in peers:
                peers.remove(peer)
                print(f"[UNREGISTERED] {peer}")
            client_socket.send("OK".encode('utf-8'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def start_discovery_server(port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen(10)
    print(f"[DISCOVERY SERVER] Running on port {port}")

    while True:
        client_socket, _ = server.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_discovery_server(5000)
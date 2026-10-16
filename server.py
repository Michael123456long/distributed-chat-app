import socket
import threading
import json
import os

# CONFIG
HOST = '127.0.0.1'
LOG_FILE = "chat.log"

clients = [] # list of client sockets on this server
peer_servers = [] # connections to other server nodes
lock = threading.Lock()

def broadcast(message, sender_socket=None):
    # Send to local clients
    with lock:
        for c in clients[:]:
            if c!= sender_socket:
                try:
                    c.send(message.encode('utf-8'))
                except:
                    clients.remove(c)
    # Forward to peer servers
    for peer in peer_servers:
        try:
            peer.send(message.encode('utf-8'))
        except:
            pass
    # Persist
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")

def handle_client(conn, addr):
    print(f"[NEW CLIENT] {addr} connected")
    with lock:
        clients.append(conn)
    while True:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if not msg: break
            # If message came from peer server, don't loop
            if msg.startswith("[PEER]"):
                msg = msg.replace("[PEER]", "")
            else:
                msg = f"[PEER]{msg}" # Mark when forwarding to peers

            print(f"Broadcast: {msg}")
            broadcast(msg, conn if "[PEER]" not in msg else None)
            # Actually send clean version
            clean_msg = msg.replace("[PEER]", "")
            # Re-broadcast clean to local clients is already done

        except:
            break
    with lock:
        if conn in clients:
            clients.remove(conn)
    conn.close()
    print(f"[DISCONNECT] {addr}")

def handle_peer(conn):
    while True:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if not msg: break
            # Message from other server -> broadcast to my clients
            broadcast(msg)
        except:
            break

def connect_to_peer(peer_host, peer_port):
    while True:
        try:
            s = socket.socket()
            s.connect((peer_host, peer_port))
            peer_servers.append(s)
            print(f"[PEER CONNECTED] {peer_host}:{peer_port}")
            threading.Thread(target=handle_peer, args=(s,), daemon=True).start()
            break
        except:
            print(f"Retrying peer {peer_port}...")
            threading.Event().wait(2)

def start_server(my_port, peer_port=None):
    server = socket.socket()
    server.bind((HOST, my_port))
    server.listen()
    print(f"[SERVER STARTED] Listening on {HOST}:{my_port}")

    if peer_port:
        threading.Thread(target=connect_to_peer, args=(HOST, peer_port), daemon=True).start()

    while True:
        conn, addr = server.accept()
        # First message decides if it's a client or server? We treat all as client for simplicity
        # In real impl, peer also calls accept, so we detect
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# RUN: python server.py 5000 5001 -> Server A connects to B
if __name__ == "__main__":
    import sys
    my_port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    peer = int(sys.argv[2]) if len(sys.argv) > 2 else None
    start_server(my_port, peer)
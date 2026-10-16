import socket
import threading
import sys

HOST = '127.0.0.1'
SERVERS = [5000, 5001] # Try in order - this is failover

def receive(sock):
    while True:
        try:
            msg = sock.recv(1024).decode('utf-8').replace("[PEER]", "")
            if msg:
                print(f"\n{msg}\nYou: ", end="")
        except:
            print("\n[Server down, trying failover...]")
            return False

def start_client():
    username = input("Enter username: ")
    sock = None
    # FAULT TOLERANCE: Try servers one by one
    for port in SERVERS:
        try:
            s = socket.socket()
            s.connect((HOST, port))
            sock = s
            print(f"[CONNECTED to Server {port}]")
            break
        except:
            print(f"Server {port} unavailable, trying next...")

    if not sock:
        print("All servers down!")
        return

    # Start listening thread
    threading.Thread(target=receive, args=(sock,), daemon=True).start()

    while True:
        try:
            text = input("You: ")
            if text.lower() == "quit": break
            full_msg = f"{username}: {text}"
            sock.send(full_msg.encode('utf-8'))
        except:
            # Reconnect logic
            for port in SERVERS:
                try:
                    sock = socket.socket()
                    sock.connect((HOST, port))
                    print(f"[RECONNECTED to Server {port}]")
                    threading.Thread(target=receive, args=(sock,), daemon=True).start()
                    break
                except:
                    continue
            else:
                break

if __name__ == "__main__":
    start_client()
import socket
import threading
import time
import traceback

TCP_PORT = 5050
SCAN_TIMEOUT = 0.4


def get_local_ip():
    """Get the active LAN IP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

import socket
import threading
from queue import Queue

SCAN_TIMEOUT = 0.3   # seconds
TCP_PORT = 1500      # target port

def scan_range(subnet, local_ip, start, end, result_queue, stop_event):
    """Scans a subrange of IPs in a subnet."""
    for i in range(start, end):
        if stop_event.is_set():
            break  # stop if another thread found a connection

        target = subnet + str(i)
        if target == local_ip:
            continue

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SCAN_TIMEOUT)
        try:
            s.connect((target, TCP_PORT))
            print(f"[CLIENT] Connected to server at {target}")
            result_queue.put(s)
            stop_event.set()  # signal success to other threads
            return
        except (socket.timeout, ConnectionRefusedError):
            s.close()
        except Exception as e:
            print(f"[DEBUG] Error connecting to {target}: {e}")
            s.close()
    # no connection found in this range
    return

def try_connect_subnet(local_ip, num_threads=8):
    subnet = ".".join(local_ip.split(".")[:-1]) + "."
    print(f"[SCAN] Searching {subnet}0–255 for active servers...")

    # Setup coordination tools
    result_queue = Queue()
    stop_event = threading.Event()
    threads = []

    # Split IP range (0–255) into roughly equal chunks
    chunk_size = 255 // num_threads
    for t in range(num_threads):
        start = t * chunk_size
        end = 255 if t == num_threads - 1 else (t + 1) * chunk_size
        thread = threading.Thread(
            target=scan_range,
            args=(subnet, local_ip, start, end, result_queue, stop_event),
            daemon=True
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads or an early success
    for thread in threads:
        thread.join()

    # If any connection succeeded, return that socket
    if not result_queue.empty():
        return result_queue.get()

    print("[SCAN] No active servers found.")
    return None

def start_server(local_ip):
    """Start a TCP server waiting for a connection."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((local_ip, TCP_PORT))
    s.listen(1)
    print(f"[SERVER] Waiting for a connection on {local_ip}:{TCP_PORT}...")
    conn, addr = s.accept()
    print(f"[SERVER] Connected with {addr[0]}")
    return conn


def listen(conn):
    """Background thread to receive messages."""
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print("[INFO] Peer disconnected.")
                break
            print(f"\n[PEER] {data.decode()}")
        except Exception as e:
            print(f"[ERROR] Listening error: {e}")
            traceback.print_exc()
            break


def safe_send(conn, msg):
    """Attempt to send a message safely."""
    try:
        conn.sendall(msg.encode())
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")
        traceback.print_exc()
        return False
local_ip = get_local_ip()

# --- MAIN ---
conn = try_connect_subnet(local_ip)

if not conn:
    print("[ROLE] No server detected — becoming server.")
    conn = start_server(local_ip)
else:
    print("[ROLE] Acting as client.")

# Disable timeout — switch back to blocking mode
conn.settimeout(None)

# Start listener thread
threading.Thread(target=listen, args=(conn,), daemon=True).start()

# Chat loop
while True:
    msg = input().strip()
    if not msg:
        continue
    if msg.lower() in ("exit", "quit"):
        print("[INFO] Closing connection.")
        conn.close()
        break
    if not safe_send(conn, msg):
        print("[INFO] Connection lost — exiting.")
        break

try:
    import os,time,sys,random,datetime,traceback,socket,threading,json,string
    from datetime import datetime
    from queue import Queue
    try:
        server_ip = open("server_ip.txt","r").read().strip()
    except:
        open("server_ip.txt","w")
        server_ip = ""
    connected = False
    if server_ip:
        try:
            socket.inet_aton(server_ip)
            print("Cached server ip found at " + server_ip+ ", attempting connection")
            conn=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(5)
            server_port=55000
            try:
                conn.connect((server_ip,server_port))
                print("connected sucessfully to "+ server_ip)
                connected = True
            except socket.timeout:
                print("connection timed out, searching for server...")
        except:
            print("saved ip address unavailable, searching for server on local subnet")
            
    if not connected:    
        TCP_PORT = 55000
        SCAN_TIMEOUT = 0.4

        def get_local_ip():
            """Get the active LAN IP."""
            conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                conn.connect(("8.8.8.8", 80))
                ip = conn.getsockname()[0]
            finally:
                conn.close()
            return ip

        def scan_range(subnet, local_ip, start, end, result_queue, stop_event):
            """Scans a subrange of IPs in a subnet."""
            for i in range(start, end):
                if stop_event.is_set():
                    break  # stop if another thread found a connection

                target = subnet + str(i)
                
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.settimeout(SCAN_TIMEOUT)
                try:
                    conn.connect((target, TCP_PORT))
                    print(f" Connected to server at {target}")
                    result_queue.put((conn,target))
                    stop_event.set()  # signal success to other threads
                    return
                except (socket.timeout, ConnectionRefusedError):
                    conn.close()
                except Exception as e:
                    print(f"[DEBUG] Error connecting to {target}: {e}")
                    conn.close()
            # no connection found in this range
            return

        def try_connect_subnet(local_ip, num_threads=32):
            subnet = ".".join(local_ip.split(".")[:-1]) + "."

            # Setup coordination tools
            result_queue = Queue()
            stop_event = threading.Event()
            threads = []

            # Split IP range (0–255) into roughly equal chunks
            chunk_size = 256 // num_threads
            for t in range(num_threads):
                start = t * chunk_size
                end = 255 if t == num_threads - 1 else (t + 1) * chunk_size
                thread = threading.Thread(
                    target=scan_range,
                    args=(subnet, local_ip, start, end, result_queue, stop_event),daemon=True)
                threads.append(thread)
                thread.start()

            # Wait for all threads or an early success
            for thread in threads:
                thread.join()

            # If any connection succeeded, return that socket
            if not result_queue.empty():
                return result_queue.get()

            print("no active servers found")
            return None

        local_ip = get_local_ip()

        # --- MAIN ---
        loop = True
        print(f"[SCAN] Searching for active servers...")
        while loop:
            result = try_connect_subnet(local_ip)
            if result:
                conn = result[0]
                server_ip = result[1]
                if conn:
                    loop = False
    open("server_ip.txt","w").write(server_ip)

    token = ""
    try:
        open("token.txt","x")
        
        if "token_backup.txt" in os.listdir("."):
            token = open("token_backup.txt","r").read()
            
            open("token.txt","w").write(token)

            print("token restored from backup")
        else:
            print("Token file created.")
    except:
        print("token found.")
        token = open("token.txt","r").read()

    username = input("Enter username: ")
    

    if not token:
        token = "NONE"

    def save_token(token):
        with open('token.txt','w') as f:
            f.write(token)
        with open('token_backup.txt','w') as f:
            f.write(token)

    handshake = f"HANDSHAKE {username}:{token}"
    conn.send(handshake.encode())
    response = conn.recv(1024).decode()
    print(f"Server response: {response}")
    print(response)
    if response.startswith("OK"):
        print("Authentication successful!")

        if "REGISTERED" in response:
            parts = response.split()
            if len(parts) == 3: 
                new_token = parts[2]
                save_token(new_token)

        while True:
            message = input("You: ")
            if message.lower() == 'quit':
                break
            conn.send(message.encode())
            data = conn.recv(1024)
            print(f"Server: {data.decode()}")
    else:
        print("Authentication failed")
            
except:
    traceback.print_exc()

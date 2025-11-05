try:
    import os,time,sys,random,datetime,traceback,socket,threading,json,string,secrets
    from datetime import datetime
    from pathlib import Path
    from queue import Queue
    #server
    self = "server"
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
        
    TOKENS_FILE = "tokens.txt"
    TOKENS_BACKUP = "tokens_backup.txt"

    # Default token that's always available
    DEFAULT_TOKENS = {
        "default": {
            "token": "0",
            "created": "PC"
        },
    }

    def load_tokens():
        # Try to load main tokens file
        if Path(TOKENS_FILE).exists():
            try:
                with open(TOKENS_FILE, 'r') as f:
                    load = json.load(f)
                
                # Backup the good file
                with open(TOKENS_BACKUP, "w") as file:
                    json.dump(load, file, indent=2)
                
                return load
                
            except Exception as e:
                traceback.print_exc()
                print("tokens file corrupt, loading backup...")
                
                # Try to load backup
                if Path(TOKENS_BACKUP).exists():
                    try:
                        with open(TOKENS_BACKUP, "r") as file:
                            load = json.load(file)
                        
                        print("backup found, restoring main file from backup")
                        with open(TOKENS_FILE, "w") as file:
                            json.dump(load, file, indent=2)
                        
                        return load
                    except:
                        print("backup also corrupt, using default")
        
        # Main file doesn't exist or is corrupt
        if Path(TOKENS_BACKUP).exists():
            try:
                with open(TOKENS_BACKUP, "r") as file:
                    load = json.load(file)
                
                print("restoring from backup")
                with open(TOKENS_FILE, "w") as file:
                    json.dump(load, file, indent=2)
                
                return load
            except:
                print("backup corrupt, using default")
        
        # Nothing works, create and return default
        print("no valid tokens file, creating default")
        with open(TOKENS_FILE, "w") as f:
            json.dump(DEFAULT_TOKENS, f, indent=2)
        
        return DEFAULT_TOKENS

    def save_tokens(tokens):
        with open(TOKENS_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)

    def generate_token():
        return secrets.token_urlsafe(32)

    def handle_handshake(conn, tokens):
        data = conn.recv(1024).decode()
        
        try:
            # Expected format: "HANDSHAKE username:token"
            if not data.startswith("HANDSHAKE "):
                conn.send(b"ERROR Invalid handshake format")
                return None
            
            parts = data[10:].split(':', 1)
            username = parts[0].strip()
            token = parts[1].strip() if len(parts) > 1 else ""
            
            # Validate username
            if not username or len(username) > 32 or not username.isalnum():
                conn.send(b"ERROR Invalid username (alphanumeric, max 32 chars)")
                return None
            # New user (no token provided)
            if not token or token == "NONE":
                if username in tokens:
                    # Username taken, suggest alternatives
                    suggestions = f"{username}2,x{username},xX{username}Xx,1144{username}"
                    conn.send(f"ERROR Username taken. Try: {suggestions}".encode())
                    return None
                else:
                    # Register new user
                    new_token = generate_token()
                    tokens[username] = {
                        "token": new_token,
                        "created": str(socket.gethostname()) 
                    }
                    save_tokens(tokens)
                    conn.send(f"OK REGISTERED {new_token}".encode())
                    print(f"New user registered: {username}")
                    return username
            
           # Existing user with token
            else:
                if username in tokens:
                    if tokens[username]["token"] == token:
                        # Correct token
                        conn.send(b"OK AUTHENTICATED")
                        print(f"User authenticated: {username}")
                        return username
                    else:
                        # Wrong token
                        conn.send(b"ERROR Invalid token for username")
                        return None
                else:
                    # Username doesn't exist register with provided token
                    tokens[username] = {
                        "token": token,
                        "created": str(socket.gethostname())
                    }
                    save_tokens(tokens)
                    conn.send(b"OK REGISTERED")
                    print(f"New user registered: {username}")
                    return username
        
        except Exception as e:
            traceback.print_exc()
            print("marker beta")
            conn.send(f"ERROR {str(e)}".encode())
            return None    
            
    sockets = []
    server_ip = get_local_ip()
    login_port = 55000
    ports = []
    
    for i in range(55001,55051):
        ports.append(i)

    class connection:
        def __init__(self):
            self.socket = ""
            self.conn = ""
            self.address = ""
            self.thread = ""
            
    connected_users = []
    
    # -----------------------------
    # Connection handshake
    # -----------------------------
    messages = []
    new_messages = []
    def listening(conn):
        global new_messages
        global sockets
        while True:
            data = conn.recv(2048)
            if data:
                new_messages.append(data.decode())
    
    def assignment():
        try:
            global ports
            global server_ip
            global login_port
            global connected_users
            global sockets
            while True:
                #make blank connection object
                print("Waiting for new connection...")
                new = connection()
                main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                main_socket.bind((server_ip,login_port))
                main_socket.listen(16)
                
                conn,address=main_socket.accept()#new user connects to server
                #assign port to user         
                port = random.choice(ports)
                ports.remove(port)
                conn.send(str(port).encode())
                #make new socket for user using assigned port
                new.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                new.socket.bind((server_ip,port))
                new.socket.listen(16)
                conn,address = new.socket.accept()#user accepts new connection
                #assign attributes to user connection object
                new.conn = conn
                new.address = address
                sockets.append(new)

                print("user connected, curent users:"+str(len(sockets)))

                main_socket.close()
                
                tokens = load_tokens()
                username = handle_handshake(new.conn, tokens)
                
                if username:
                    connected_users.append(username)

                    new_thread = threading.Thread(target=listening,args=(new.conn,), daemon=True)
                    new.thread = new_thread
                    new.thread.start()
                
        except:
            print("marker charlie")
            traceback.print_exc()
                    

    thread = threading.Thread(target=assignment,args=(), daemon=True)
    thread.start()


    while True:
        if messages != new_messages:
            for user in sockets:
                messages = new_messages.copy()
                user.conn.send(messages[len(messages)-1].encode())
    
except:
    print("marker delta")
    traceback.print_exc()
    
        
























        




    


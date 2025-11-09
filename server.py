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
            
    users = []
    server_ip = get_local_ip()
    login_port = 55000

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
    messages = Queue()
    
    def listening(user):
        global messages
        global users
        global connected_users

        try:
            with user.conn as conn:
                while True:
                    data = conn.recv(2048)
                    if not data:
                        break  # graceful disconnect

                    # Instead of append → use put
                    messages.put((user, data.decode()))

        except Exception as e:
            print(f"user {getattr(user, 'address', '?')} disconnected unexpectedly: {e}")

        finally:
            if user in users:
                users.remove(user)
            if hasattr(user, "username") and user.username in connected_users:
                connected_users.remove(user.username)
            print(f"user disconnected, current users: {len(users)}")

    #if user authentication fails, manage the error, either disconnect or new username
    #if user disconnects, maybe try reconnect? or just kick em
    #update pygame gui

    def assignment():
        try:
            global server_ip
            global login_port
            global connected_users
            global users

            main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            main_socket.bind((server_ip, login_port))
            main_socket.listen(16)
            print(f"Server listening on {server_ip}:{login_port}")

            while True:
                print("Waiting for new connection...")
                new = connection()
                conn, address = main_socket.accept()
                new.conn = conn
                new.address = address
                users.append(new)
                print("User connected, current users: " + str(len(users)))
                tokens = load_tokens()
                username = handle_handshake(new.conn, tokens)
                if username:
                    connected_users.append(username)
                    new_thread = threading.Thread(target=listening, args=(new,), daemon=True)
                    new.thread = new_thread
                    new.thread.start()

        except:
            print("marker charlie")
            traceback.print_exc()
                    
    thread = threading.Thread(target=assignment,args=(), daemon=True)
    thread.start()


    while True:
        try:
            sender, msg = messages.get()
            for user in users:
                if user != sender:
                    user.conn.send(msg.encode())
        except Exception as e:
            print("error sending message", e)
    
except:
    print("marker delta")
    traceback.print_exc()
    
        
























        




    


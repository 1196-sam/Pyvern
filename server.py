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
    def load_tokens():
        if Path(TOKENS_FILE).exists():
            with open(TOKENS_FILE, 'r') as f:
                try:
                    load = json.load(f)
                    f.close()
                    with open(TOKENS_BACKUP,"w") as file:
                        json.dump(load, file, indent=2)
                        file.close()
                    return(load)
                except:
                    print("marker alpha")
                    traceback.print_exc()
                    f.close()
                    print("tokens file corrupt, loading backup...")
                    if TOKENS_BACKUP in os.listdir("."):
                        with open (TOKENS_BACKUPS,"r") as file:
                            load = json.load(file)
                            file.close()
                        print("backup found, restoring main file from backup")
                        with open(TOKENS_FILE,"w") as file:
                            json.dump(tokens, file, indent=2)
                            return(load)
                    else:
                        return()
        else:
            if TOKENS_BACKUP in os.listdir("."):
                with open (TOKENS_BACKUPS,"r") as file:
                    load = json.load(file)
                    file.close()
                print("tokens file missing, restoring tokens from backup")
                with open(TOKENS_FILE,"w") as file:
                    json.dump(tokens, file, indent=2)
                    return(load)
            else:
                open("tokens.txt","w")
                return()    
        return {}

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
    
    for i in range(55000,55050):
        ports.append(i)

    class connection:
        def __init__(self):
            self.socket = ""
            self.conn = ""
            self.address = ""
    
    # -----------------------------
    # Connection handshake
    # -----------------------------
    def assignment():
        try:
            global ports
            global server_ip
            global login_port
            global sockets
            while True:
                #make blank connection object
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
                    with new.conn:
                        while True:
                            try:
                                data = conn.recv(2048)
                                if not data:
                                    break
                                print(f"{username}: {data.decode()}")
                                new.conn.sendall(f"Echo: {data.decode()}".encode())
                            except:
                                break
                        print(f"{username} disconnected")
                else:
                    conn.close()                
                print("Waiting for new connection...")
                
        except:
            print("marker charlie")
            traceback.print_exc()
                    
    thread = threading.Thread(target=assignment,args=(), daemon=True)
    thread.start()








    flag = False
    while True:#main
        None
     
except:
    print("marker delta")
    traceback.print_exc()
    
        
























        




    

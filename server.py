try:
    import os,time,sys,random,datetime,traceback,socket,threading,json,string
    from datetime import datetime
    #server
    self = "server"
    def spin(message: str, duration: float, interval: float = 0.1):
        symbols = "|/-\\"
        end_time = time.time() + duration
        i = 0
        try:
            while time.time() < end_time:
                sys.stdout.write(f"\r{message} {symbols[i % len(symbols)]}")
                sys.stdout.flush()
                time.sleep(interval)
                i += 1
        finally:
            sys.stdout.write(f"\r{message} ✓\n")
            sys.stdout.flush()

    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    print("\033c")
    spin("Starting server", 3)
    print("\033c")
    logo = '''
 /$$$$$$$                                                         
| $$__  $$                                                        
| $$  \ $$ /$$   /$$ /$$    /$$ /$$$$$$   /$$$$$$  /$$$$$$$       
| $$$$$$$/| $$  | $$|  $$  /$$//$$__  $$ /$$__  $$| $$__  $$      
| $$____/ | $$  | $$ \  $$/$$/| $$$$$$$$| $$  \__/| $$  \ $$      
| $$      | $$  | $$  \  $$$/ | $$_____/| $$      | $$  | $$      
| $$      |  $$$$$$$   \  $/  |  $$$$$$$| $$      | $$  | $$      
|__/       \____  $$    \_/    \_______/|__/      |__/  |__/      
           /$$  | $$                                              
          |  $$$$$$/                                              
           \______/                                               
  /$$$$$$                                                         
 /$$__  $$                                                        
| $$  \__/  /$$$$$$   /$$$$$$  /$$    /$$ /$$$$$$   /$$$$$$       
|  $$$$$$  /$$__  $$ /$$__  $$|  $$  /$$//$$__  $$ /$$__  $$      
 \____  $$| $$$$$$$$| $$  \__/ \  $$/$$/| $$$$$$$$| $$  \__/      
 /$$  \ $$| $$_____/| $$        \  $$$/ | $$_____/| $$            
|  $$$$$$/|  $$$$$$$| $$         \  $/  |  $$$$$$$| $$            
 \______/  \_______/|__/          \_/    \_______/|__/            
                                                                  
                                                                  
    '''
    lines = logo.strip('\n').splitlines()
    
    for line in lines:
        print(line)
        time.sleep(0.1) 

    class chat():
        def __init_(self):
            self.name = ""
            self.messages = []
            self.users = []


    def receive_data(csc_):#receive message sent to server and send it to all users
        while True:
            data = csc.recv(1024)
            for s in sockets:
                s.send(data)
            if data:
                messages.append(data.decode())
    
    def send_chat(csc_,messages): #when user connects, send them the chat so far
        y = str(messages)
        y = y.encode('utf-8')
        csc.sendall(y)


    def manager():
        for s in sockets: #run as background thread for each user
            def socket_manager():
                receive_data()
                send_data()
                ping_connection()
            
    sockets = []
    count = 0
    chats = []
    
    for files in os.listdir("."):
        if "###" in files:
            new = chat()
            new.name = files.replace("###","")
            new.messages = files.unpickle
            chats.append(new)

    server_ip = get_local_ip()
    print(f"You are running on {server_ip} for a quick connection, ask users to use this IP to connect to.`")

    login_port = 55000
    
    ports = []
    
    for i in range(55000,55050):
        ports.append(i)

    class connection:
        def __init__(self):
            self.socket = ""
            self.csc = ""
            self.address = ""

    def assignment():
        try:
            global ports
            global server_ip
            global login_port
            global sockets
            while True:
                print("Starting....")
                new = connection()
                main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                main_socket.bind((server_ip,login_port))
                main_socket.listen(16)
                csc,address=main_socket.accept()
                port = random.choice(ports)
                ports.remove(port)
                csc.send(str(port).encode())
                new.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sockets.append(new)
                index = len(sockets)-1
                sockets[index].socket.bind((server_ip,port))
                sockets[index].socket.listen(16)
                csc,address=sockets[index].socket.accept()
                sockets[index].csc = csc
                sockets[index].address = address
                main_socket.close()
        except:
            traceback.print_exc()
            
    print("Starting Thread...")
    thread = threading.Thread(target=assignment,args=(), daemon=True)
    thread.start()

        

    TOKEN_FILE = 'token.json'

    # -----------------------------
    # File Handling
    # -----------------------------
    def init_token_file():
        """Ensure token.json exists."""
        if not os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'w') as f:
                json.dump({}, f, indent=4)

    def load_tokens():
        """Load token data from disk."""
        init_token_file()
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)

    def save_tokens(tokens):
        """Save token data to disk."""
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f, indent=4)

    # -----------------------------
    # Token / Tag Generators
    # -----------------------------
    def generate_token(length=12):
        """Generate a unique permanent token (identity key)."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def generate_tag():
        """Generate a 4-digit discriminator tag."""
        return f"{random.randint(0, 9999):04d}"

    # -----------------------------
    # Handshake System
    # -----------------------------
    def handshake(username=None, tag=None, provided_token=None, client_ip=None):
        """
        Handle user authentication/creation.
        - No token → create new identity.
        - With token → authenticate and update username/tag if changed.
        """
        tokens = load_tokens()

        # New user: no token provided
        if provided_token is None:
            new_token = generate_token()
            new_tag = tag if tag else generate_tag()

            tokens[new_token] = {
                "username": username if username else "Unnamed",
                "tag": new_tag,
                "last_seen_ip": client_ip
            }
            save_tokens(tokens)

            print(f"New identity created: {username}#{new_tag} with token {new_token}")
            return new_token, "new_identity"

        # Existing user: token provided
        if provided_token in tokens:
            user = tokens[provided_token]
            changed = False

            if username and username != user["username"]:
                user["username"] = username
                changed = True
            if tag and tag != user["tag"]:
                user["tag"] = tag
                changed = True
            if client_ip and client_ip != user.get("last_seen_ip"):
                user["last_seen_ip"] = client_ip
                changed = True

            if changed:
                save_tokens(tokens)
                print(f"Updated identity for {provided_token}: {user['username']}#{user['tag']}")

            print(f"Authenticated as {user['username']}#{user['tag']}")
            return provided_token, "authenticated"

        # Invalid token
        print(f"Invalid token: {provided_token}")
        return None, "invalid_token"
    while True:
        None
    """
    while True:#main
        if sockets[len(sockets)] == []:
            sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            server_ip = '127.0.0.1'
            sockets[count] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sockets[count].bind((server_ip,socket_port))
            sockets[count].listen(16)
        
            csc, address=sockets[0].accept()
            #send_chat(csc_,messages)
            count += 1
            socket_port += 1
    """
            
except Exception as error:
    traceback.print_exc()
    
        
























        




    

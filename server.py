try:
    import os,random,datetime,traceback,socket,threading
    from datetime import datetime
    #server
    self = "server"
    
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

    server_ip = "192.168.0.70"
    
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
        global ports
        global server_ip
        global login_port
        global sockets
        while True:
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
            
    thread = threading.Thread(target=assignment,args=(), daemon=True)
    thread.start()

    while True:
        text = input(">:")
        for sock in sockets:
            sock.csc.send(text.encode())
        


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
    
    

























        




    

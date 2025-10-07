def run():
    try:
        import os,random,datetime,traceback,socket,threading,string
        from datetime import datetime
        #server
        self = "server"
        
        def gentoken():
            import random,string
            length = 16
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
            print(token)
        gentoken()


        class chat():
            def __init_(self):
                self.name = ""
                self.messages = []
                self.users = []

        # # receive_data(csc_):#receive message sent to server and send it to all users
        #     while True:
        #     data = csc.recv(1024)
        #     for s in sockets:
        #         s.send(data)
        #     if data:
        #         messages.append(data.decode())
        
        send_chat(csc_,messages): #when user connects, send them the chat so far
            y = str(messages)
            y = y.encode('utf-8')
            csc.sendall(y)

        for s in sockets: #run as background thread for each user
            def socket_manager():
                receive_data()
                send_data()
                ping_connection()

        
        sockets = []
        count = 0
        socket_port=1500

        chats = []
        
        for files in os.listdir("."):
            if "###" in files:
                new = chat()
                new.name = files.replace("###","")
                new.messages = files.unpickle
                chats.append(new)
                
                
        while True:
            sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            socket_ip = '127.0.0.1'
            sockets[count] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sockets[count].bind((socket_ip,socket_port))
            sockets[count].listen(16)
            
            csc, address=sockets[0].accept()
            #send_chat(csc_,messages)
            count += 1
            socket_port += 1
            print(len(sockets))
    
        



    except Exception as error:
        traceback.print_exc()
        

        
run()

















            




        

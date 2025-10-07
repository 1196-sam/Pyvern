def run():
    print("started")
    try:
        import pygame,os,random,datetime,traceback,socket,threading,sys
        from datetime import datetime
        
        # Known IPs for each machine
        main_ip='192.168.0.65'

        vm_ip='192.168.0.70'

        socket_port=6598

        def get_local_ip():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Doesn't actually send data — just figures out the outbound interface
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            finally:
                s.close()
            return ip

        own_ip = get_local_ip()

        """
        if own_ip == main_ip:
            device_name = "Main PC"
            socket_ip = vm_ip
            
        elif own_ip == vm_ip:
            device_name = "Virtual Machine"
            socket_ip = main_ip
            
        else:
            device_name = "Unknown Device"
            socket_ip = None"""

        socket_ip = main_ip
        
        device_name = "asdf"
        print(f"Local IP: {own_ip}")
        print(f"Device role: {device_name}")
        if socket_ip:
            print(f"Peer IP to connect to: {socket_ip}")
        else:
            print("No matching peer found.")    


        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        
        if own_ip == main_ip:
            socket.bind((socket_ip,socket_port))
            socket.listen(16)
            csc, address=socket.accept()
        else:
            socket.connect((socket_ip,socket_port))
        
        
        pygame.init()
        screen = pygame.display.set_mode()
        size = screen.get_size()
        pygame.display.quit()
        width = size[0]
        height = size[1]
        text = ""
        width = width//4
        height = height//2
        screen = pygame.display.set_mode([width,height])

        BLACK = [0,0,0]
        CYAN = [0,255,255]
        RED = [255,0,0]
        BLUE = [0,0,255]
        GREY = [50,50,50]
        GREEN = [0,255,0]
        WHITE = [255,255,255]
        font_size = height//20
        font = pygame.font.SysFont("ARIAL.TTF",font_size)
        clock = pygame.time.Clock()

        def render_text(text_,colour,location):
            newtext = font.render(str(text_),True,colour)
            screen.blit(newtext,location)

        

        allowed = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r",
                   "s","t","u","v","w","x","y","z"," ","1","2","3","4","5","6","7","8","9","0"]

        messages = [""]
        own_messages = []
        def listen_for_messages(socket):
            while True:
                try:
                    data = socket.recv(1024)
                    if not data:
                        break  # connection closed
                    messages.append(data.decode())
                except:
                    break


        thread = threading.Thread(target=listen_for_messages,args=(socket,), daemon=True)
        thread.start()

        

        frames = 0
        delete = False
        while True:
            clock.tick(20)
            if delete:
                text = text[:-1]
            screen.fill(BLACK)
            for event in pygame.event.get():
                if event.type == pygame.quit:
                    pygame.QUIT()
                if event.type == pygame.KEYDOWN:
                    print(event.key)
                    if event.key == pygame.K_RETURN:
                        typing = False
                        message = message+str(datetime.now())
                        socket.sendall(message.encode())
                        messages.append(message)
                        text = ""
                    if event.key == 8:
                        delete = True
                    else:
                        if event.unicode in allowed:
                            text += event.unicode

                if event.type == pygame.KEYUP:
                    if event.key == 8:
                        delete = False
            y = 0
            for message in messages:
                render_text(message,GREEN,[0,y])
                y += font_size+font_size/5
            pygame.draw.rect(screen,GREY,[0,height-font_size,width,font_size])
            render_text(text,GREEN,[0,height-font_size])
            pygame.display.flip()
        
    except Exception as error:
        traceback.print_exc()
        
        


























            




        

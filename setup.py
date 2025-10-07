import os
import sys
# Check if pip is available
try:
    import pip
except ImportError:
    print("pip is not installed. Please install Python & pip first.")
    sys.exit(1)

# Run pip install
print("Installing required packages...")
os.system("curl -O https://raw.githubusercontent.com/1196-sam/py-lan-chat/refs/heads/main/requirements.txt")
os.system(f"{sys.executable} -m pip install -r requirements.txt")
print("All dependencies installed!")


print("""
############################
# Welcome to PyChat Setup! #
############################
""")
import os

def ServerSetup():
    if not os.path.exists('server.py'):
        print("server.py not found downloading server files.")
        os.system("curl -O https://raw.githubusercontent.com/1196-sam/py-lan-chat/refs/heads/main/server.py")
    else:
        print("server.py found")

    if not os.path.exists('backup.txt'):
        print("No backup file found creating backup.txt...")
        with open('backup.txt', 'w') as f:
            f.write("")  
    else:
        print("backup.txt found")

    if not os.path.exists('config.json'):
        print("config.json not found creating config.json...")
        with open('config.json', 'w') as f:
            f.write("{}")  
    else:
        print("config.json found")

    if os.path.exists('server.py') and os.path.exists('backup.txt') and os.path.exists('config.json'):
        print("All files found")
        answer = input('Would you like to start the Server now?(Answer "Y" or "N")\n>')
        match answer.lower():
            case "y":
                import server
                server.run()
            case "n":
                print('Ok, Server not started. Exiting Setup...')
            case other:
                print('Answer not given...\nDefaulting to No...')
                print('Ok, Server not started. Exiting Setup...')


def ClientSetup():
    if not os.path.exists('chat.py'):
        print('Chat files not found...\n Downloading Chat files...')
        os.system("curl -O https://raw.githubusercontent.com/1196-sam/py-lan-chat/refs/heads/main/chat.py")
    else:
        print('chat.py found')
    if not os.path.exists('secret.json'):
        print('No Token file found.\nCreating Token file.')
        with open('secret.json','w') as f:
            f.write("{}")
    else:
        print('Token found.')
        
    if not os.path.exists('userconfig.json'):
        print('No Userconfig file found.\nCreating UserConfig file.')
        with open('userconfig.json','w') as f:
            f.write("{}")
    else:
        print('UserConfig found.')

    if os.path.exists('chat.py') and os.path.exists('secret.json') and os.path.exists('userconfig.json'):
        print("All files found starting chat...")
        answer = input('Would you like to start the Chat now?(Answer "Y" or "N")\n>')
        match answer.lower():
            case "y":
                import chat
                chat.run()
            case "n":
                print('Ok, chat not started. Exiting Setup...')
            case other:
                print('Answer not given...\nDefaulting to No...')
                print('Ok, chat not started. Exiting Setup...')


        

mode = input('Please type "Y" for server, "N" for client. \n The default is SERVER\n>')

match mode.lower():
    case "y":
        ServerSetup()
    case "n":
        ClientSetup()
    case other:
        ServerSetup()




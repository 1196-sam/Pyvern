import os
import sys
import chat
# Check if pip is available
try:
    import pip
except ImportError:
    print("pip is not installed. Please install Python & pip first.")
    sys.exit(1)

# Run pip install
print("Installing required packages...")
os.system(f"{sys.executable} -m pip install -r requirements.txt")
print("All dependencies installed!")


print("""
############################
# Welcome to PyChat Setup! #
############################
""")

def ServerSetup():
    files = os.listdir('.')
    if 'backup.txt' in files:
        print('message backup found')
        if 'config.json' in files:
            print('Server config file found.')
        else:
            open('config.json','w')
            print('config file not found...\nOne has been created for you in the current directory.')
            ServerSetup()
    else:
        open('backup.txt','w')
        print('No backup file found...\n One has been created for you in the current directory.')
        ServerSetup()

def ClientSetup():
    files = os.listdir('.')
    if 'secret.json' in files:
        print('Token found')
        if 'userconfig.json' in files:
            print('User generated config found.')
            chat.run()
        else:
            print('User config not found.\n Generating...')
            open('userconfig.json',"w")
            ClientSetup()
    else:
        print('Token not found...\n Generating file for token when conected to server.')
        open('secret.json','w')
        ClientSetup()



mode = input('Please type "Y" for server, "N" for client. \n The default is SERVER\n>')

match mode.lower():
    case "y":
        ServerSetup()
    case "n":
        ClientSetup()
    case other:
        ServerSetup()



print('Server created')

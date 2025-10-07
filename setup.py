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

mode = input('Please type "Y" for server, "N" for client. \n The default is SERVER\n>')

match mode.lower():
    case "y":
        ServerSetup() # ADD SERVER LATER
    case "n":
        print("client") # ADD CLIENT LATER
    case other:
        print('server') # ADD SERVER LATER



print('Server created')

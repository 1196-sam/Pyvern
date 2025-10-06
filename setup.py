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

mode = input('Please type "Y" for server, "N" for client. \n The default is SERVER\n>')

match mode.lower():
    case "y":
        print('server') # ADD SERVER LATER
    case "n":
        print("client") # ADD CLIENT LATER
    case other:
        print('server') # ADD SERVER LATER

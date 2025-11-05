Hello! 
This is a project by 1144oli and 1196-sam. Which is a lan chat made entirely in python.
It uses a server and client model although peer to peer is in the works. If port forwarded this can be a web chat, although we suggest using it as just a lan chat for now as it's the only use case we've tested for.

# Usage
Usage has been made as easy as possible. Simply download the setup.py and nohting else. Python3 is required for this project to work with PIP installed as the package manager.

## Installing Python with pip
### Windows 
Please go to https://www.python.org/ and download the lastest version.
**In the install wizard please make sure you select pip.**

### Arch Linux 
To download python on arch linux please run: 
```
sudo pacman -Syu 
sudo pacman -S python python-pip
```

### Debian based systems (Ubuntu)
```
sudo apt update
sudo apt install python3 
sudo apt install python3-pip -y
```
### RHEL based Distros (Fedora & Centos)
```
sudo dnf install python3
sudo dnf install python3-pip
```
## Running the setup script
1) Download Setup.py to a newly made Folder.
2) Run in the directory
```
python3 setup.py
```
3) Follow the setup procedure.
4) Configure server and client to your best wishes this is done in config.json and userconfig.json respectively. There are 50 max connections by default. 
6) Use chat.py to connect on a client.
